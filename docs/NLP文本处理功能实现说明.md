# NLP文本处理功能实现说明

## 功能概述

为会议转录添加NLP（自然语言处理）功能，对Whisper转录的原始文本进行智能优化处理。

## 处理内容

### 1. 文本结构化
- **分段优化**：根据语义将长句合理分段
- **标点恢复**：为缺少标点的句子添加合适的标点符号
- **口语化修正**：将口语表达转换为更专业的书面语

### 2. 语义理解
- 识别关键议题和主题
- 提取重要信息点
- 理解上下文关联

### 3. 多语言支持
- 处理中英文混合场景
- 确保语义连贯性
- 保持专业术语的准确性

## 实现方案

### 方案一：AI驱动的NLP处理（推荐）

使用AI模型进行智能文本处理，优点是处理质量高、适应性强。

#### 实现步骤

1. **添加NLP处理函数**

在 `backend/routers/meetings.py` 的第397行之前添加以下函数（完整代码见`NLP文本处理函数.py`）：

```python
async def process_transcript_with_nlp(speakers: List[SpeakerSegment], ai_config) -> List[SpeakerSegment]:
    """
    使用NLP对转录文本进行处理
    """
    # ... (见NLP文本处理函数.py)
```

2. **在转录流程中调用NLP处理**

找到 `process_meeting_file` 函数中转录完成的部分（大约在第600行附近），在保存转录结果之前添加NLP处理：

```python
# Whisper转录完成后
logger.info("转录完成，开始NLP文本处理...")

# 进行NLP处理
ai_config = await db.ai_configs.find_one({"is_enabled": True})
if ai_config:
    speaker_segments = await process_transcript_with_nlp(speaker_segments, ai_config)
    logger.info("NLP文本处理完成")
else:
    logger.warning("未配置AI，跳过NLP处理")

# 然后保存处理后的转录结果
update_data = {
    "status": MeetingStatus.WAITING_CONFIRMATION,
    "speakers": [s.dict() for s in speaker_segments],  # 保存NLP处理后的文本
    "transcript_file_path": transcript_file_path,
    "updated_at": get_beijing_time()
}
```

### 方案二：规则基础的NLP处理

如果不想使用AI，可以使用基于规则的方法：

```python
def simple_nlp_processing(text: str) -> str:
    """简单的文本处理"""
    import re
    
    # 1. 移除多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 2. 添加基本标点（简单规则）
    # 在句子结尾添加句号
    text = re.sub(r'([^。！？\.\!\?])(\s+[A-Z])', r'\1。\2', text)
    
    # 3. 修正常见口语表达
    replacements = {
        '嗯': '',
        '啊': '',
        '呃': '',
        '那个': '',
        '这个': '',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # 4. 移除重复词
    text = re.sub(r'(\w+)\1+', r'\1', text)
    
    return text
```

## 集成位置

### 在 `process_meeting_file` 函数中

找到转录完成的代码块（大约在第580-620行），修改如下：

```python
# 原代码：
# 2. 使用Whisper进行转录 (自动分段)
logger.info("开始使用Whisper进行转录...")
# ... Whisper转录代码 ...

# 添加NLP处理：
logger.info("转录完成，开始NLP文本处理...")

# 获取AI配置
ai_config = await db.ai_configs.find_one({"is_enabled": True})

if ai_config:
    try:
        # 使用AI进行NLP处理
        speaker_segments = await process_transcript_with_nlp(speaker_segments, ai_config)
        logger.info("✅ NLP文本处理完成")
    except Exception as nlp_error:
        logger.warning(f"NLP处理失败，使用原始文本: {nlp_error}")
else:
    logger.info("未配置AI，跳过NLP处理，使用原始转录文本")

# 保存转录文本到文件 (保存NLP处理后的文本)
transcript_lines = []
for segment in speaker_segments:
    speaker_name = segment.speaker_name or f"说话人{segment.speaker_id}"
    time_str = f"[{segment.start_time:.1f}s - {segment.end_time:.1f}s]"
    transcript_lines.append(f"{speaker_name} {time_str}: {segment.text}")

transcript_content = "\n".join(transcript_lines)
# ... 保存文件 ...
```

## 效果对比

### 处理前（原始Whisper输出）：
```
说话人1 [0.0s - 5.2s]: 嗯那个我们今天主要讨论一下这个项目的进度啊然后看看有什么问题
说话人2 [5.5s - 12.3s]: 好的呃目前来看整体进度还可以但是有几个地方需要注意一下
```

### 处理后（NLP优化）：
```
说话人1 [0.0s - 5.2s]: 我们今天主要讨论项目的进度，看看有什么问题。
说话人2 [5.5s - 12.3s]: 好的。目前来看，整体进度还可以，但是有几个地方需要注意。
```

## 配置选项

可以在AI配置中添加NLP处理的开关：

```python
{
    "api_key": "...",
    "base_url": "...",
    "model": "...",
    "is_enabled": true,
    "enable_nlp": true,  # 新增：是否启用NLP处理
    "nlp_level": "standard"  # 新增：处理级别 (light/standard/deep)
}
```

## 性能考虑

1. **处理时间**：NLP处理会增加额外的AI调用时间（约5-15秒）
2. **成本**：每次NLP处理会消耗一次AI API调用
3. **可选性**：建议设置为可选功能，用户可以选择是否启用

## 测试建议

1. **上传测试视频**
2. **等待转录完成**
3. **查看转录文本文件**，对比NLP处理前后的差异
4. **生成智能纪要**，查看基于优化文本的纪要质量

## 注意事项

1. **保持原意**：NLP处理不应改变原始内容的含义
2. **时间戳保持**：处理后保持原有的时间戳信息
3. **说话人信息**：保持原有的说话人标识
4. **错误处理**：NLP处理失败时应回退到原始文本
5. **日志记录**：详细记录处理过程，便于调试

## 扩展功能

未来可以添加：

1. **情感分析**：识别说话人的情绪和态度
2. **主题提取**：自动识别讨论的主要主题
3. **关键词提取**：提取会议中的关键术语
4. **摘要生成**：为每个片段生成简短摘要
5. **实体识别**：识别人名、地名、组织名等

---

**创建时间**: 2026-01-09
**版本**: v1.0
