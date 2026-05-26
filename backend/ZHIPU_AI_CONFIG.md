# 智谱AI配置说明

## 🎯 智谱AI (GLM) 配置

智谱AI提供了兼容OpenAI格式的API,可以直接使用。

### 配置参数

在系统设置 → AI配置中填写:

| 参数 | 值 | 说明 |
|------|-----|------|
| **API Key** | 你的智谱API Key | 从智谱AI控制台获取 |
| **Base URL** | `https://open.bigmodel.cn/api/paas/v4` | 智谱AI的API地址 |
| **Model** | `glm-4` 或 `glm-3-turbo` | 推荐使用glm-4 |

### 示例配置

```json
{
  "api_key": "your-zhipu-api-key.xxxxxxxxx",
  "base_url": "https://open.bigmodel.cn/api/paas/v4",
  "model": "glm-4",
  "is_enabled": true
}
```

## 📝 智谱AI模型选择

### GLM-4 (推荐)
- **优势**: 最新模型,效果最好
- **速度**: 中等
- **成本**: 较高
- **适用**: 需要高质量会议纪要

### GLM-3-Turbo
- **优势**: 速度快,成本低
- **速度**: 快
- **成本**: 低
- **适用**: 快速生成,对质量要求不高

## 🔧 常见问题

### 1. API调用失败

**错误**: "摘要生成失败: API返回错误 401"

**原因**: API Key错误或已过期

**解决**:
1. 检查API Key是否正确
2. 登录智谱AI控制台确认API Key有效
3. 检查API Key是否有足够的额度

### 2. 网络连接失败

**错误**: "摘要生成失败: 网络请求失败"

**原因**: 无法连接到智谱AI服务器

**解决**:
1. 检查网络连接
2. 确认Base URL是否正确
3. 检查防火墙设置

### 3. 超时错误

**错误**: "摘要生成失败: 请求超时"

**原因**: 会议内容太长,AI处理时间超过120秒

**解决**:
1. 尝试使用更快的模型(glm-3-turbo)
2. 分段处理长会议
3. 重新生成摘要

### 4. 响应格式错误

**错误**: "摘要生成失败: 响应格式错误"

**原因**: API返回的数据格式不符合预期

**解决**:
1. 检查Base URL是否正确
2. 确认使用的是兼容OpenAI格式的API
3. 查看详细日志了解具体错误

## 📊 智谱AI vs OpenAI

| 特性 | 智谱AI | OpenAI |
|------|--------|--------|
| 语言支持 | 中文优秀 | 英文优秀 |
| 访问速度 | 国内快 | 国内慢 |
| 成本 | 较低 | 较高 |
| 模型选择 | GLM系列 | GPT系列 |
| API兼容性 | 兼容OpenAI | 原生 |

## 🚀 获取智谱API Key

1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册/登录账号
3. 进入控制台
4. 创建API Key
5. 复制API Key到系统配置

## 💡 优化建议

### 1. 选择合适的模型

**短会议(< 30分钟)**:
- 使用 `glm-3-turbo`
- 速度快,成本低

**长会议(> 30分钟)**:
- 使用 `glm-4`
- 质量高,理解能力强

### 2. 控制会议长度

**建议**:
- 单次会议不超过2小时
- 超长会议建议分段上传

### 3. 监控API额度

**定期检查**:
- 登录智谱AI控制台
- 查看API调用次数和余额
- 及时充值

## 📝 日志示例

### 成功调用
```
INFO - 调用AI接口: https://open.bigmodel.cn/api/paas/v4, 模型: glm-4
INFO - 发送请求到: https://open.bigmodel.cn/api/paas/v4/chat/completions
INFO - 请求payload大小: 15234 字符
INFO - AI响应状态码: 200
INFO - AI摘要生成成功,长度: 1523 字符
```

### 失败调用
```
INFO - 调用AI接口: https://open.bigmodel.cn/api/paas/v4, 模型: glm-4
INFO - 发送请求到: https://open.bigmodel.cn/api/paas/v4/chat/completions
INFO - 请求payload大小: 15234 字符
ERROR - AI API返回错误状态码 401: {"error": "invalid api key"}
```

## 🔍 调试步骤

### 1. 检查配置
```bash
# 查看AI配置
mongo
use project_management
db.ai_configs.find().pretty()
```

### 2. 测试API连接
```bash
curl -X POST https://open.bigmodel.cn/api/paas/v4/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

### 3. 查看详细日志
```bash
# 查看最新日志
tail -f backend/logs/app.log

# Windows PowerShell
Get-Content backend/logs/app.log -Wait -Tail 50
```

## ✅ 配置检查清单

- [ ] API Key已正确填写
- [ ] Base URL为 `https://open.bigmodel.cn/api/paas/v4`
- [ ] Model为 `glm-4` 或 `glm-3-turbo`
- [ ] is_enabled设置为true
- [ ] API Key有足够的额度
- [ ] 网络可以访问智谱AI服务器
- [ ] 已重启后端服务

## 🎉 总结

**智谱AI配置要点**:
- ✅ 使用正确的Base URL
- ✅ 选择合适的模型
- ✅ 确保API Key有效
- ✅ 监控API额度
- ✅ 查看详细日志

**现在重启后端服务,查看详细日志,找出具体的错误原因!** 🚀
