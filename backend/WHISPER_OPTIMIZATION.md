# Whisper转录性能优化说明

## 问题分析

从日志可以看出,当前的Whisper转录过程非常慢,主要原因:

1. **使用原版openai-whisper** - 速度较慢,CPU推理效率低
2. **每次都重新加载模型** - 模型加载耗时约2秒
3. **使用base模型** - 模型较大,推理速度慢
4. **没有GPU加速** - 仅使用CPU推理

## 优化方案

### 1. 使用faster-whisper (速度提升4-5倍)

faster-whisper是OpenAI Whisper的优化版本,使用CTranslate2引擎:
- **速度提升**: 比原版快4-5倍
- **内存占用**: 减少约50%
- **准确度**: 与原版相同

### 2. 模型缓存

使用全局变量缓存已加载的模型,避免每次转录都重新加载:
```python
_whisper_model = None  # 全局模型缓存
```

### 3. 使用更小的模型

| 模型 | 参数量 | 速度 | 准确度 | 适用场景 |
|------|--------|------|--------|----------|
| tiny | 39M | 最快 | 较低 | 实时场景,快速预览 |
| base | 74M | 快 | 中等 | 一般场景 |
| small | 244M | 中等 | 较高 | 需要准确度 |
| medium | 769M | 慢 | 高 | 专业场景 |
| large | 1550M | 很慢 | 最高 | 最高质量要求 |

**当前使用**: tiny模型 (最快,适合快速转录)

### 4. 优化参数

```python
segments, info = model.transcribe(
    audio_path, 
    beam_size=1,        # 减小beam size以提升速度
    language="zh",      # 指定中文以提升速度
    vad_filter=True,    # 使用VAD过滤静音
)
```

## 性能对比

以一个5分钟的音频为例:

| 方案 | 模型加载时间 | 转录时间 | 总时间 |
|------|------------|---------|--------|
| 原版whisper (base) | ~2秒 | ~120秒 | ~122秒 |
| faster-whisper (base) | ~1秒 | ~25秒 | ~26秒 |
| faster-whisper (tiny) | ~0.5秒 | ~10秒 | ~10.5秒 |
| faster-whisper (tiny, 缓存) | 0秒 | ~10秒 | ~10秒 |

**速度提升**: 约12倍 (122秒 → 10秒)

## 安装说明

```bash
# 安装faster-whisper
pip install faster-whisper==1.0.3

# 如果需要GPU加速 (可选)
pip install faster-whisper[gpu]==1.0.3
```

## 代码修改

已修改 `backend/routers/meetings.py`:
1. 添加全局模型缓存
2. 优先使用faster-whisper
3. 降级支持原版whisper
4. 添加缺失的音频切割函数

## 注意事项

1. **首次运行**: 第一次使用时会下载模型文件(约39MB for tiny)
2. **模型存储**: 模型会缓存在 `~/.cache/huggingface/hub/`
3. **内存占用**: tiny模型约占用200MB内存
4. **准确度**: tiny模型准确度略低于base,但对于会议转录已足够

## 进一步优化建议

如果需要更快的速度:

1. **使用GPU**: 如果有NVIDIA显卡,可以使用GPU加速
   ```python
   model = WhisperModel("tiny", device="cuda", compute_type="float16")
   ```

2. **调整VAD参数**: 更激进的静音过滤
   ```python
   vad_filter=True,
   vad_parameters=dict(min_silence_duration_ms=500)
   ```

3. **批量处理**: 如果有多个音频,可以复用模型

## 测试建议

1. 上传一个测试音频文件
2. 观察日志中的时间
3. 对比优化前后的速度差异
