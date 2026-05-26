# 知识库文件预览 - 临时公开URL接口

## 新增接口说明

### 1. 生成临时公开URL
**接口**: `GET /api/knowledge/{knowledge_id}/public-url`

**功能**: 为知识库文档生成一个临时的公开访问URL，供Office Online等外部服务使用。

**请求参数**:
- `knowledge_id`: 文档ID（路径参数）
- `expires_minutes`: 有效期（分钟），默认10分钟（查询参数）

**响应示例**:
```json
{
  "public_url": "http://114.66.56.200:6004/api/knowledge/public/abc123...",
  "temp_token": "abc123...",
  "expires_at": "2026-01-05T17:10:00",
  "expires_in_seconds": 600
}
```

### 2. 公开访问文件
**接口**: `GET /api/knowledge/public/{temp_token}`

**功能**: 通过临时令牌访问文件，无需认证。

**特性**:
- ✅ 无需认证
- ✅ 支持跨域（CORS）
- ✅ 自动设置正确的Content-Type
- ✅ 令牌过期自动清理

## 使用流程

### 前端调用示例

```javascript
// 1. 生成临时公开URL
const generatePublicUrl = async (docId) => {
  try {
    const token = localStorage.getItem("token");
    const response = await axios.get(
      `/api/knowledge/${docId}/public-url`,
      {
        params: { expires_minutes: 10 },
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    const { public_url } = response.data;
    
    // 2. 使用Office Online预览
    const officeOnlineUrl = `https://view.officeapps.live.com/op/view.aspx?src=${encodeURIComponent(public_url)}`;
    
    // 3. 打开新窗口
    window.open(officeOnlineUrl, '_blank');
    
    ElMessage.success('正在使用Office Online打开文档...');
  } catch (error) {
    ElMessage.error('生成预览链接失败');
  }
};
```

### 完整的前端实现

```vue
<template>
  <el-button 
    type="success" 
    size="small" 
    @click="previewWithOfficeOnline(currentKnowledge)"
    :loading="generatingUrl"
  >
    使用Office Online预览
  </el-button>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';

const generatingUrl = ref(false);

const previewWithOfficeOnline = async (doc) => {
  generatingUrl.value = true;
  
  try {
    // 1. 生成临时公开URL
    const token = localStorage.getItem("token");
    const response = await axios.get(
      `/api/knowledge/${doc.id}/public-url`,
      {
        params: { expires_minutes: 10 },
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    const { public_url, expires_in_seconds } = response.data;
    
    // 2. 构建Office Online URL
    const officeOnlineUrl = `https://view.officeapps.live.com/op/view.aspx?src=${encodeURIComponent(public_url)}`;
    
    // 3. 打开新窗口
    window.open(officeOnlineUrl, '_blank');
    
    ElMessage.success({
      message: `预览链接已生成，有效期${Math.floor(expires_in_seconds / 60)}分钟`,
      duration: 3000
    });
  } catch (error) {
    console.error('生成预览链接失败:', error);
    ElMessage.error('生成预览链接失败，请稍后重试');
  } finally {
    generatingUrl.value = false;
  }
};
</script>
```

## 安全性说明

### 1. 令牌安全
- 使用`secrets.token_urlsafe(32)`生成安全的随机令牌
- 令牌长度32字节，足够安全
- 每个令牌只能访问一个特定文件

### 2. 时效性
- 默认10分钟有效期
- 过期自动清理
- 可根据需要调整有效期

### 3. 访问控制
- 生成URL需要认证
- 公开访问仅限于已生成令牌的文件
- 令牌过期后无法访问

### 4. 生产环境建议
```python
# 使用Redis存储令牌（推荐）
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# 存储令牌
redis_client.setex(
    f"temp_token:{temp_token}",
    expires_minutes * 60,
    json.dumps(token_info)
)

# 获取令牌
token_data = redis_client.get(f"temp_token:{temp_token}")
```

## 配置说明

### 1. 添加BASE_URL配置

在`backend/config.py`中添加：

```python
class Settings(BaseSettings):
    # ... 其他配置
    
    # 服务器公网地址（用于生成公开URL）
    BASE_URL: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
```

在`.env`文件中设置：

```env
# 生产环境
BASE_URL=http://114.66.56.200:6004

# 或使用域名
BASE_URL=https://your-domain.com
```

### 2. Nginx配置

确保Nginx允许大文件和跨域访问：

```nginx
location /api/knowledge/public/ {
    proxy_pass http://backend:8000/api/knowledge/public/;
    
    # 允许跨域
    add_header 'Access-Control-Allow-Origin' '*';
    add_header 'Access-Control-Allow-Methods' 'GET, OPTIONS';
    
    # 支持大文件
    client_max_body_size 3072M;
    proxy_read_timeout 300s;
}
```

## 优势

1. **✅ 安全**: 临时令牌，自动过期
2. **✅ 灵活**: 可自定义有效期
3. **✅ 简单**: 无需复杂配置
4. **✅ 兼容**: 支持Office Online等外部服务
5. **✅ 高效**: 内存存储，响应快速

## 限制

1. **⚠️ 内存存储**: 重启服务器令牌丢失（生产环境建议用Redis）
2. **⚠️ 公网访问**: Office Online需要能访问公网地址
3. **⚠️ 文件大小**: Office Online对文件大小有限制（通常10MB）

## 故障排查

### 问题1: Office Online显示错误
**原因**: 
- 公网地址无法访问
- 令牌已过期
- 文件格式不支持

**解决**:
- 确认BASE_URL配置正确
- 增加有效期
- 检查文件格式

### 问题2: 跨域错误
**原因**: CORS配置问题

**解决**:
```python
# 在返回FileResponse时添加CORS头
headers={
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS"
}
```

### 问题3: 文件下载而不是预览
**原因**: Content-Type设置不正确

**解决**:
```python
# 确保使用正确的media_type
media_type = mimetypes.guess_type(file_name)[0]
```

## 总结

这个接口提供了一个简单而安全的方式，让Office Online等外部服务能够访问需要认证的文件。通过临时令牌机制，既保证了安全性，又提供了灵活性。
