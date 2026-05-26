# 会议分析系统 - OSS对象存储集成完整指南

## 📋 功能概述

本次更新为会议分析系统添加了OSS对象存储支持，解决了阿里云语音识别API需要公网URL访问音频文件的问题。

### 核心功能
1. ✅ 支持阿里云OSS和腾讯云COS
2. ✅ 可选配置，未配置时自动使用本地服务器URL
3. ✅ 完整的配置管理界面
4. ✅ 连接测试功能
5. ✅ 敏感信息掩码保护

---

## 🔧 后端实现

### 1. 配置文件 (`backend/config.py`)

新增配置项：
```python
# OSS对象存储配置
OSS_PROVIDER: Optional[str] = None  # aliyun, tencent, 或 None
OSS_ACCESS_KEY_ID: Optional[str] = None
OSS_ACCESS_KEY_SECRET: Optional[str] = None
OSS_BUCKET_NAME: Optional[str] = None
OSS_REGION: Optional[str] = None
OSS_ENDPOINT: Optional[str] = None  # 自定义域名(可选)
```

### 2. 配置API (`backend/routers/config.py`)

新增接口：
- `GET /api/config/oss` - 获取OSS配置
- `POST /api/config/oss` - 保存OSS配置
- `POST /api/config/oss/test` - 测试OSS连接

### 3. OSS工具模块 (`backend/utils/oss_utils.py`)

核心函数：
```python
async def upload_file_to_oss(local_file_path: str, object_name: str = None) -> str:
    """
    上传文件到OSS
    - 如果配置了OSS: 上传到云存储并返回公网URL
    - 如果未配置OSS: 返回本地服务器URL
    """
```

支持的云服务商：
- **阿里云OSS**: 使用 `oss2` SDK
- **腾讯云COS**: 使用 `cos-python-sdk-v5` SDK

---

## 🎨 前端实现

### 配置界面 (`frontend/src/views/ASRConfig.vue`)

新增"OSS对象存储配置"卡片，包含：

#### 1. OSS提供商选择
- 不使用OSS(本地)
- 阿里云OSS
- 腾讯云COS

#### 2. 配置项
- **Access Key ID**: OSS访问密钥ID
- **Access Key Secret**: OSS访问密钥
- **Bucket名称**: 存储桶名称
- **区域**: OSS区域 (如: cn-hangzhou, ap-guangzhou)
- **自定义域名**: 可选，如已绑定自定义域名

#### 3. 功能按钮
- **保存OSS配置**: 保存配置到服务器
- **测试连接**: 验证OSS配置是否正确
- **重置**: 重新加载配置

---

## 📦 依赖安装

### 阿里云OSS
```bash
pip install oss2
```

### 腾讯云COS
```bash
pip install cos-python-sdk-v5
```

### 一次性安装
```bash
pip install oss2 cos-python-sdk-v5
```

---

## 🚀 使用指南

### 场景1: 使用阿里云OSS

1. **获取阿里云OSS凭证**
   - 登录阿里云控制台
   - 进入OSS服务
   - 创建Bucket
   - 获取Access Key ID和Secret

2. **配置系统**
   - 访问 `/asr-config` 页面
   - 在"OSS对象存储配置"部分：
     - 选择"阿里云OSS"
     - 填写Access Key ID
     - 填写Access Key Secret
     - 填写Bucket名称 (如: my-meeting-bucket)
     - 填写区域 (如: cn-hangzhou)
     - (可选) 填写自定义域名

3. **测试并保存**
   - 点击"测试连接"验证配置
   - 测试成功后点击"保存OSS配置"

### 场景2: 使用腾讯云COS

1. **获取腾讯云COS凭证**
   - 登录腾讯云控制台
   - 进入COS服务
   - 创建存储桶
   - 获取SecretId和SecretKey

2. **配置系统**
   - 访问 `/asr-config` 页面
   - 选择"腾讯云COS"
   - 填写相应配置
   - 区域格式: ap-guangzhou, ap-beijing等

### 场景3: 不使用OSS (本地模式)

- 选择"不使用OSS(本地)"或留空
- 系统将使用本地服务器URL
- **注意**: 需确保服务器公网可访问

---

## 🔄 工作流程

### 会议音频上传流程

```
1. 用户上传会议文件
   ↓
2. 系统提取音频
   ↓
3. 检查OSS配置
   ├─ 已配置OSS
   │  ├─ 上传音频到云存储
   │  └─ 生成云存储公网URL
   └─ 未配置OSS
      └─ 生成本地服务器URL
   ↓
4. 调用阿里云语音识别API
   ↓
5. 获取转录结果
```

### OSS上传逻辑

```python
# 在 meetings.py 中使用
from utils.oss_utils import upload_file_to_oss

# 上传音频文件
audio_url = await upload_file_to_oss(
    local_file_path=audio_path,
    object_name=f"meetings/{meeting_id}/audio.wav"
)

# audio_url 将是:
# - OSS配置时: https://bucket.oss-cn-hangzhou.aliyuncs.com/meetings/xxx/audio.wav
# - 未配置时: http://your-server.com:8000/uploads/meetings/xxx/audio.wav
```

---

## ⚙️ 配置示例

### 阿里云OSS配置示例

```env
OSS_PROVIDER=aliyun
OSS_ACCESS_KEY_ID=LTAI5t...
OSS_ACCESS_KEY_SECRET=xxx...
OSS_BUCKET_NAME=my-meeting-bucket
OSS_REGION=cn-hangzhou
OSS_ENDPOINT=  # 可选，留空使用默认域名
```

### 腾讯云COS配置示例

```env
OSS_PROVIDER=tencent
OSS_ACCESS_KEY_ID=AKIDxxx...
OSS_ACCESS_KEY_SECRET=xxx...
OSS_BUCKET_NAME=my-meeting-1234567890
OSS_REGION=ap-guangzhou
OSS_ENDPOINT=  # 可选
```

### 本地模式配置

```env
OSS_PROVIDER=  # 留空或不设置
# 其他OSS配置项可以不设置
```

---

## 🔒 安全特性

### 1. 敏感信息掩码
- Access Key ID: 显示为 `LTAI****...****5678`
- Access Key Secret: 显示为 `xxx****...****xyz`
- 前端不回填原始密钥

### 2. 可选更新
- 修改其他配置时，可以不重新输入密钥
- 留空密钥字段将保持原值不变

### 3. 权限控制
- 只有管理员可以查看和修改OSS配置
- 普通用户无法访问配置页面

---

## 🐛 故障排除

### 问题1: 测试连接失败 - 缺少SDK

**错误信息**:
```
缺少SDK库: No module named 'oss2'
```

**解决方案**:
```bash
# 阿里云
pip install oss2

# 腾讯云
pip install cos-python-sdk-v5
```

### 问题2: 上传失败 - 权限错误

**可能原因**:
- Access Key权限不足
- Bucket不存在
- 区域配置错误

**解决方案**:
1. 检查Access Key是否有OSS/COS的读写权限
2. 确认Bucket名称正确
3. 确认区域配置正确

### 问题3: 阿里云语音识别无法访问音频

**可能原因**:
- OSS Bucket未设置公共读权限
- 自定义域名配置错误

**解决方案**:
1. 在OSS控制台设置Bucket为公共读
2. 或配置正确的自定义域名

---

## 📊 性能优势

### 使用OSS的优势

| 特性 | 本地模式 | OSS模式 |
|------|---------|---------|
| 公网访问稳定性 | ⚠️ 依赖服务器网络 | ✅ 云服务商保障 |
| 带宽消耗 | ⚠️ 占用服务器带宽 | ✅ 使用OSS带宽 |
| 存储成本 | ✅ 免费(本地存储) | ⚠️ 按量计费 |
| 扩展性 | ⚠️ 受限于磁盘 | ✅ 几乎无限 |
| CDN加速 | ❌ 不支持 | ✅ 支持 |

---

## 🔄 升级路径

### 从本地模式升级到OSS

1. 安装SDK依赖
2. 配置OSS参数
3. 测试连接
4. 保存配置
5. 新上传的会议将自动使用OSS

**注意**: 已有的会议音频不会自动迁移到OSS

---

## 📝 API文档

### GET /api/config/oss

获取OSS配置

**响应**:
```json
{
  "provider": "aliyun",
  "access_key_id_masked": "LTAI****5678",
  "access_key_secret_masked": "xxx****xyz",
  "bucket_name": "my-bucket",
  "region": "cn-hangzhou",
  "endpoint": ""
}
```

### POST /api/config/oss

保存OSS配置

**请求**:
```json
{
  "provider": "aliyun",
  "access_key_id": "LTAI...",
  "access_key_secret": "xxx...",
  "bucket_name": "my-bucket",
  "region": "cn-hangzhou",
  "endpoint": ""
}
```

### POST /api/config/oss/test

测试OSS连接

**响应**:
```json
{
  "success": true,
  "message": "阿里云OSS连接成功!"
}
```

---

## 🎯 最佳实践

### 1. 生产环境建议
- ✅ 使用OSS提高稳定性
- ✅ 配置CDN加速
- ✅ 定期清理过期音频文件
- ✅ 设置Bucket生命周期规则

### 2. 开发环境建议
- ✅ 可以使用本地模式节省成本
- ✅ 确保开发服务器有公网IP
- ✅ 或使用内网穿透工具(如ngrok)

### 3. 安全建议
- ✅ 使用子账号Access Key
- ✅ 限制Access Key权限范围
- ✅ 定期轮换Access Key
- ✅ 启用OSS访问日志

---

## 📞 技术支持

如遇到问题，请检查：
1. SDK是否正确安装
2. Access Key权限是否正确
3. Bucket和区域配置是否匹配
4. 网络连接是否正常

---

**更新时间**: 2026-01-27  
**版本**: v2.1 - OSS集成版
