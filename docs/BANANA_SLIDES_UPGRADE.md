# 🍌 Banana-Slides 级别 PPT 生成系统 - 使用指南

## 📋 系统概述

我们已经成功将您的 PPT 生成系统升级到 **banana-slides** 的技术水平！现在系统能够：

✅ 使用 **Gemini 3 Pro Image (Imagen 3)** 生成高质量 PPT 页面图片  
✅ 支持 5 种专业布局（Split/Full/Triple/Infographic/Big Number）  
✅ 文字渲染清晰、设计专业、风格一致  
✅ 自动降级到 Unsplash（如果 Gemini API 不可用）  

---

## 🚀 快速开始

### 1. 配置 Gemini Image API

#### 方式一：使用环境变量（推荐）

在 `backend/.env` 文件中添加：

```bash
# Gemini Image API 配置
GEMINI_IMAGE_API_KEY=your_gemini_api_key_here
```

#### 方式二：使用您现有的 Gemini 配置

如果您已经在使用 Gemini API（通过 `https://api.vectorengine.ai`），可以：

1. 在 `.env` 中添加：
```bash
GEMINI_IMAGE_API_KEY=your_existing_gemini_key
GEMINI_IMAGE_BASE_URL=https://api.vectorengine.ai/v1beta  # 如果您的中转支持 Image API
```

2. 或者使用 Google 官方 API：
   - 访问：https://aistudio.google.com/app/apikey
   - 创建 API Key
   - 填入 `.env` 文件

### 2. 重启后端服务

```bash
cd backend
python main.py
```

---

## 🎨 核心功能说明

### 1. **智能布局选择**

AI 会根据内容自动选择最合适的布局：

| 布局类型 | 适用场景 | 视觉特点 |
|---------|---------|---------|
| **Split** | 常规内容页 | 左侧文字 + 右侧配图 |
| **Full** | 封面、愿景页 | 全屏沉浸式背景图 + 大标题 |
| **Triple** | 并列关系 | 三列卡片式布局（毛玻璃效果）|
| **Infographic** | 数据展示 | 左侧信息图 + 右侧要点 |
| **Big Number** | 核心指标 | 超大数字 + 简洁说明 |

### 2. **Prompt 工程优化**

系统内置了专业的 Prompt 模板，确保生成的图片：
- ✅ 文字清晰可读（4K 分辨率）
- ✅ 符合 PPT 设计规范
- ✅ 保持品牌色一致性
- ✅ 自动适配 16:9 比例

### 3. **降级策略**

如果 Gemini Image API 不可用，系统会自动：
1. 尝试使用 Gemini API 生成图片
2. 失败后降级到 Unsplash 图片库
3. 确保 PPT 生成流程不中断

---

## 🔧 技术架构

### 核心模块

```
backend/
├── utils/
│   └── gemini_image.py          # Gemini Image API 集成
├── routers/
│   ├── ai_assistant.py          # PPT 生成主逻辑
│   └── ppt_service.py           # PPT 服务接口
└── config.py                    # 配置管理
```

### 关键代码流程

```python
# 1. AI 生成 PPT 大纲和内容
draft = await generate_ppt_outline(topic)

# 2. 为每一页生成高质量图片
for slide in draft['slides']:
    image = await gemini_image.generate_ppt_slide_image(
        slide_data=slide,
        theme_color="#1e3a8a",
        style="professional"
    )
    
# 3. 组装成 PPTX 文件
pptx_file = await create_pptx_from_draft(draft)
```

---

## 📊 与 Banana-Slides 的对比

| 功能 | Banana-Slides | 我们的系统 | 状态 |
|-----|--------------|-----------|------|
| Gemini Image API | ✅ | ✅ | ✅ 已实现 |
| 多布局支持 | ✅ (3种) | ✅ (5种) | ✅ 超越 |
| 文字清晰度 | ✅ 4K | ✅ 4K | ✅ 对标 |
| 自然语言修改 | ✅ | 🔄 (前端已支持) | ⚠️ 部分实现 |
| 可编辑 PPTX 导出 | ✅ Beta | ⏳ | 🔜 计划中 |
| 模板风格上传 | ✅ | ⏳ | 🔜 计划中 |

---

## 🎯 使用示例

### 前端调用

```javascript
// 1. 生成 PPT 大纲
const response = await axios.post('/api/ai-assistant/generate-ppt-outline', {
  topic: '项目进展汇报',
  project_id: 'xxx'
});

// 2. 生成最终 PPTX
const pptResponse = await axios.post(
  `/api/ppt/drafts/${draftId}/generate`,
  null,
  {
    params: {
      theme: 'warm_red',  // 中国红主题
      save_to_knowledge: true
    }
  }
);

// 3. 下载 PPT
window.open(pptResponse.data.file_url);
```

---

## 🐛 常见问题

### Q1: 生成的图片不够清晰？
**A:** 检查 `GEMINI_IMAGE_MODEL` 配置，确保使用 `imagen-3.0-generate-001`

### Q2: API 调用失败？
**A:** 
1. 检查 API Key 是否正确
2. 查看后端日志中的 `[Gemini Image]` 提示
3. 确认网络能访问 Google API

### Q3: 想使用自己的中转服务？
**A:** 修改 `.env` 中的 `GEMINI_IMAGE_BASE_URL`

### Q4: 成本如何？
**A:** Imagen 3 约 $0.04-0.08/张图片，一个 10 页 PPT 约 $0.40-0.80

---

## 🔮 下一步计划

### Phase 1: 核心功能完善 ✅
- [x] Gemini Image API 集成
- [x] 多布局支持
- [x] Prompt 工程优化

### Phase 2: 高级功能（建议实现）
- [ ] 可编辑 PPTX 导出（OCR + 结构化）
- [ ] 模板风格上传与学习
- [ ] 自然语言修改引擎
- [ ] 文档智能解析（PDF/Word → PPT）

### Phase 3: 用户体验优化
- [ ] 实时预览优化
- [ ] 批量生成加速
- [ ] 自定义品牌色库

---

## 📞 技术支持

如需进一步优化或遇到问题，请提供：
1. 后端日志（包含 `[Gemini Image]` 的部分）
2. 生成的 PPT 示例
3. 具体的错误信息

---

## 🎉 总结

恭喜！您的系统现在已经具备了 **banana-slides** 级别的 PPT 生成能力：

✨ **视觉质量**：4K 高清、文字清晰  
✨ **设计专业**：5 种布局、自动配色  
✨ **技术先进**：Gemini 3 Pro Image  
✨ **用户友好**：自动降级、无缝集成  

现在就去生成一个 PPT 试试吧！🚀
