# AI API调用问题排查指南

## 问题描述

从日志中看到，AI API返回了状态码200，但是响应体无法解析为JSON，导致JSONDecodeError。

```
AI响应状态码: 200
AI调用失败: JSONDecodeError - Expecting value: line 1 column 1 (char 0)
```

## 可能的原因

### 1. API返回空响应
- API返回了200状态码，但响应体为空
- 解决方案：已添加空响应检查

### 2. API返回非JSON格式
- API返回了HTML错误页面
- API返回了纯文本
- 解决方案：已添加响应文本日志记录

### 3. API认证问题
- API Key无效或过期
- Base URL配置错误
- 解决方案：检查AI配置

### 4. API兼容性问题
- 不同的AI服务提供商可能有不同的响应格式
- 解决方案：查看响应文本日志，适配不同格式

## 已添加的改进

### 1. 详细日志记录
```python
# 记录响应文本
response_text = response.text
logger.info(f"AI响应内容长度: {len(response_text)} 字符")
logger.info(f"AI响应前200字符: {response_text[:200]}")
```

### 2. 空响应检查
```python
if not response_text or len(response_text.strip()) == 0:
    logger.error("AI API返回空响应")
    return "摘要生成失败: API返回空响应"
```

### 3. JSON解析错误处理
```python
try:
    data = response.json()
except Exception as json_error:
    logger.error(f"JSON解析失败: {json_error}")
    logger.error(f"完整响应文本: {response_text}")
    return f"摘要生成失败: 响应不是有效的JSON格式"
```

## 调试步骤

### 1. 查看完整日志
重新运行后，查看日志中的以下信息：
- `AI响应内容长度`
- `AI响应前200字符`
- `完整响应文本`（如果JSON解析失败）

### 2. 检查AI配置
确认以下配置正确：
```python
{
    "api_key": "your-api-key",
    "base_url": "https://api.vectorengine.ai",  # 确认URL正确
    "model": "gemini-3-pro-preview",  # 确认模型名称正确
    "is_enabled": true
}
```

### 3. 测试API连接
可以使用curl测试API：
```bash
curl -X POST https://api.vectorengine.ai/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-3-pro-preview",
    "messages": [
      {"role": "user", "content": "测试"}
    ]
  }'
```

### 4. 检查API响应格式
不同的AI服务可能返回不同的格式：

**OpenAI格式：**
```json
{
  "choices": [
    {
      "message": {
        "content": "..."
      }
    }
  ]
}
```

**其他格式可能：**
```json
{
  "data": {
    "content": "..."
  }
}
```

## 常见问题解决方案

### 问题1：API返回HTML错误页面
**症状：** 响应文本以`<!DOCTYPE html>`或`<html>`开头

**解决方案：**
- 检查Base URL是否正确
- 检查API Key是否有效
- 检查网络代理设置

### 问题2：API返回认证错误
**症状：** 状态码401或403

**解决方案：**
- 更新API Key
- 检查API Key权限
- 确认账户余额

### 问题3：API返回限流错误
**症状：** 状态码429

**解决方案：**
- 等待一段时间后重试
- 升级API套餐
- 实现请求队列

### 问题4：响应格式不兼容
**症状：** JSON解析成功，但缺少`choices`字段

**解决方案：**
需要适配不同的API响应格式，修改代码：

```python
# 检查不同的响应格式
if "choices" in data:
    content = data["choices"][0]["message"]["content"]
elif "data" in data and "content" in data["data"]:
    content = data["data"]["content"]
elif "result" in data:
    content = data["result"]
else:
    logger.error(f"未知的响应格式: {data}")
    return "摘要生成失败: 响应格式不支持"
```

## 下一步操作

1. **重新运行测试**
   - 点击"重新生成纪要"按钮
   - 查看后端日志中的新增信息

2. **分析响应内容**
   - 查看`AI响应前200字符`
   - 如果是HTML，检查URL配置
   - 如果是JSON，检查格式是否匹配

3. **根据响应调整代码**
   - 如果API格式不同，需要适配响应解析逻辑
   - 如果是认证问题，更新API配置

## 临时测试方案

如果需要快速测试智能纪要功能，可以使用示例数据：

1. 打开 `示例智能纪要数据.json`
2. 复制JSON内容
3. 在数据库中手动更新会议记录的`summary_content`字段
4. 刷新页面查看效果

或者修改代码，临时返回示例数据：

```python
# 在generate_meeting_summary函数中临时添加
if True:  # 临时测试
    import json
    with open("示例智能纪要数据.json", "r", encoding="utf-8") as f:
        return f.read()
```

---

**更新时间**: 2026-01-09
**版本**: v1.0
