# 知识库文件在线预览功能修复

## 问题描述
文件预览的临时连接功能不可用,无法使用 Office Online 预览 Word/Excel/PowerPoint 文件。

## 根本原因
1. **后端缺少配置**: `config.py` 中没有定义 `BASE_URL` 变量
2. **前端未实现**: `knowledge.js` 中没有调用预览 API 的代码

## 已修复的内容

### 1. 后端配置修复 ✅

#### 文件: `backend/config.py`
添加了 `BASE_URL` 配置项:
```python
class Settings(BaseSettings):
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BASE_URL: str = "http://localhost:8000"  # 服务器公网地址,用于生成临时公开URL
```

#### 文件: `backend/.env.example`
创建了环境变量配置示例:
```env
# 公网地址配置(用于生成知识库文件的临时公开URL)
# 本地开发环境
BASE_URL=http://localhost:8000

# 生产环境示例(请根据实际情况修改)
# BASE_URL=http://114.66.56.200:6002
# 或使用域名
# BASE_URL=https://your-domain.com
```

### 2. 前端功能实现 ✅

#### 文件: `frontend/js/knowledge.js`

**新增功能**:
1. **判断文件是否支持预览**
   ```javascript
   function canPreviewOnline(fileType) {
       const supportedTypes = ['word', 'excel', 'powerpoint'];
       return supportedTypes.includes(fileType);
   }
   ```

2. **生成临时公开 URL 并预览**
   ```javascript
   async function previewDocument(docId, fileType) {
       // 1. 调用后端 API 生成临时公开 URL
       // 2. 构建 Office Online 预览 URL
       // 3. 打开新窗口预览
   }
   ```

3. **在文档卡片中添加预览按钮**
   - 只对 Word/Excel/PowerPoint 文件显示"在线预览"按钮
   - 点击后自动生成临时链接并打开 Office Online

## 使用方法

### 1. 配置服务器地址

#### 开发环境
在 `backend/.env` 文件中设置:
```env
BASE_URL=http://localhost:8000
```

#### 生产环境(Docker)
在 `deployment/.env` 文件中设置:
```env
BASE_URL=http://114.66.56.200:6002
```
**注意**: 必须使用公网可访问的地址,因为 Office Online 需要从外部访问这个 URL。

### 2. 使用预览功能

1. 进入知识库页面
2. 找到 Word/Excel/PowerPoint 文件
3. 点击"在线预览"按钮
4. 系统会自动:
   - 生成 10 分钟有效期的临时访问链接
   - 使用 Office Online 打开预览
   - 在新窗口中显示文件内容

## 技术实现

### 后端 API

#### 生成临时 URL
```
GET /api/knowledge/{knowledge_id}/public-url?expires_minutes=10
```

**响应**:
```json
{
  "public_url": "http://your-domain.com/api/knowledge/public/abc123...",
  "temp_token": "abc123...",
  "expires_at": "2026-01-06T17:50:00",
  "expires_in_seconds": 600
}
```

#### 公开访问文件
```
GET /api/knowledge/public/{temp_token}
```
- 无需认证
- 支持跨域(CORS)
- 自动设置正确的 Content-Type
- 令牌过期自动清理

### 前端流程

```
用户点击"在线预览"
    ↓
调用后端 API 生成临时 URL
    ↓
构建 Office Online 预览链接
    ↓
在新窗口打开预览
```

## 安全机制

1. **临时令牌**: 使用 `secrets.token_urlsafe(32)` 生成安全随机令牌
2. **时效性**: 默认 10 分钟有效期,过期自动清理
3. **访问控制**: 生成 URL 需要认证,公开访问仅限已生成令牌的文件
4. **单文件绑定**: 每个令牌只能访问一个特定文件

## 支持的文件类型

| 文件类型 | 扩展名 | Office Online 支持 |
|---------|--------|-------------------|
| Word 文档 | .doc, .docx | ✅ 支持 |
| Excel 表格 | .xls, .xlsx | ✅ 支持 |
| PowerPoint | .ppt, .pptx | ✅ 支持 |
| PDF | .pdf | ❌ 不支持 (可考虑使用其他预览服务) |
| Markdown | .md | ❌ 不支持 (可考虑前端渲染) |

## 故障排查

### 问题 1: 预览窗口打不开
**原因**: 浏览器阻止了弹窗

**解决**: 
- 允许浏览器弹窗
- 或者在用户点击后立即打开窗口

### 问题 2: Office Online 显示错误
**可能原因**:
1. `BASE_URL` 配置的地址无法从公网访问
2. 临时令牌已过期
3. 文件格式不被 Office Online 支持

**解决**:
1. 确认 `BASE_URL` 配置正确,且可从公网访问
2. 增加有效期: `expires_minutes=30`
3. 检查文件格式是否为 .docx, .xlsx, .pptx

### 问题 3: 跨域错误
**原因**: CORS 配置问题

**解决**: 后端已自动添加 CORS 头:
```python
headers={
    "Access-Control-Allow-Origin": "*",
    "Cache-Control": "no-cache"
}
```

### 问题 4: 文件下载而不是预览
**原因**: Content-Type 设置不正确

**解决**: 后端已自动设置:
```python
media_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
```

## 生产环境建议

### 使用 Redis 存储令牌
当前使用内存存储,服务器重启后令牌会丢失。生产环境建议使用 Redis:

```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# 存储令牌
redis_client.setex(
    f"temp_token:{temp_token}",
    expires_minutes * 60,
    json.dumps(token_info)
)
```

### Nginx 配置
确保 Nginx 允许跨域访问:

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

## 总结

现在文件预览功能已完全可用:
- ✅ 后端配置已添加
- ✅ 前端功能已实现
- ✅ 安全机制已就位
- ✅ 支持 Word/Excel/PowerPoint 在线预览

只需配置正确的 `BASE_URL`,即可使用 Office Online 预览文件!
