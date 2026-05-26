# ✅ AI PPT 图片生成 - 使用说明

## 🎯 当前实现

系统已升级为使用 **OpenAI 兼容的图片生成 API**，可以与您现有的 AI 配置无缝集成！

## 🔧 工作原理

### 自动配置
- ✅ 系统会从数据库中获取您配置的 AI 模型
- ✅ 使用相同的 API Key 和 Base URL
- ✅ 调用 `/images/generations` 接口生成图片
- ✅ 如果失败，自动降级到 Unsplash

### API 调用流程

```
用户生成 PPT
    ↓
从数据库获取 AI 配置
    ↓
调用: {base_url}/images/generations
    ↓
使用 DALL-E 3 或兼容模型
    ↓
生成 1792x1024 (16:9) 高清图片
    ↓
嵌入到 PPTX
```

## 📋 支持的服务

### 1. VectorEngine.AI (您当前使用的)
```
Base URL: https://api.vectorengine.ai/v1
模型: dall-e-3 (如果支持)
```

### 2. OpenAI 官方
```
Base URL: https://api.openai.com/v1
模型: dall-e-3
```

### 3. 其他兼容服务
任何支持 OpenAI Images API 格式的服务都可以使用

## 🎨 生成参数

系统使用以下参数生成图片：

```json
{
  "model": "dall-e-3",
  "prompt": "<专业的PPT页面描述>",
  "n": 1,
  "size": "1792x1024",
  "quality": "hd",
  "response_format": "b64_json"
}
```

## 📊 Prompt 工程

系统会根据不同布局生成专业的 Prompt，例如：

**Split 布局示例：**
- 左侧：标题 + 要点列表
- 右侧：专业配图
- 设计：商务风格、高对比度
- 质量：4K 分辨率

## 🔍 调试信息

后端日志会显示：

```
[Gemini Image] 调用图片生成 API: https://api.vectorengine.ai/v1/images/generations
[Gemini Image] 图片生成成功，大小: 245678 bytes
```

或者如果失败：

```
[Gemini Image] API 返回状态码: 404
[Gemini Image] 生成失败，降级为 Unsplash
```

## ⚠️ 常见问题

### Q1: 图片生成失败怎么办？

**可能原因：**
1. VectorEngine.AI 可能不支持图片生成 API
2. API Key 没有图片生成权限
3. 模型名称不正确

**解决方案：**
- 系统会自动降级到 Unsplash，不影响 PPT 生成
- 或者使用 OpenAI 官方 API（需要单独配置）

### Q2: 如何使用 OpenAI 官方 API？

在 `backend/.env` 中添加：

```bash
GEMINI_IMAGE_API_KEY=sk-your-openai-key
GEMINI_IMAGE_BASE_URL=https://api.openai.com/v1
```

### Q3: 成本如何？

- **DALL-E 3**: 约 $0.04-0.12/张图片
- **一个 10 页 PPT**: 约 $0.40-1.20

## 🚀 使用步骤

1. **确认 AI 配置** - 前端有已启用的配置
2. **生成 PPT** - 正常使用功能
3. **查看效果** - 自动尝试 AI 图片，失败则用 Unsplash

## 📈 效果对比

**使用 AI 生成图片：**
- ✅ 文字清晰可读
- ✅ 与内容完美匹配
- ✅ 专业设计布局

**降级到 Unsplash：**
- ✅ 高质量摄影图片
- ⚠️ 可能与内容不完全匹配

---

**现在就去试试吧！** 🎨 系统会自动处理一切！
