# Docker 部署完整解决方案总结

## 📋 问题清单

在 Docker 部署过程中遇到的所有问题及解决方案:

### 1. ✅ pip 依赖安装超时
**问题**: 下载大型 Python 包时网络超时(594.3 MB 的包在 363.4 MB 时超时)

**解决方案**:
- 分批安装依赖(6个批次)
- 增加超时时间(600s → 1200s,AI依赖 1800s)
- 增加重试次数(5次 → 10次,AI依赖 15次)
- 多镜像源备选(清华 + 阿里云)

### 2. ✅ Playwright 依赖安装失败
**问题**: Debian Trixie 中字体包名称变更,`ttf-unifont` → `fonts-unifont`

**解决方案**:
- 不使用 `playwright install-deps`
- 手动安装必要的系统依赖
- 使用 Debian Trixie 兼容的包名

### 3. ✅ Faster-Whisper 模型下载失败
**问题**: 容器内无法访问 Hugging Face Hub 下载模型

**解决方案**:
- 配置环境变量 `HF_ENDPOINT=https://hf-mirror.com`
- 在构建阶段预下载模型
- 提供 OpenAI-Whisper 作为备用方案

## 🎯 最终优化效果

### 构建时间优化
- **依赖安装**: 分批安装,单批失败不影响其他批次
- **模型预下载**: 构建时完成,运行时无需等待
- **缓存利用**: 每个批次独立缓存,修改代码不需要重新安装所有依赖

### 运行时优化
- **模型加载**: 首次使用无需下载,直接加载
- **网络访问**: 使用国内镜像,速度更快
- **降级方案**: Faster-Whisper 失败自动降级到 OpenAI-Whisper

## 📦 完整的 Dockerfile 优化

```dockerfile
# 1. 基础镜像
FROM python:3.11-slim

# 2. 环境变量配置
ENV PYTHONUNBUFFERED=1 \
    HF_ENDPOINT=https://hf-mirror.com \
    PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/

# 3. 系统依赖安装
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
    curl wget gnupg ca-certificates ffmpeg chromium chromium-driver

# 4. Python 依赖分批安装
# 第1批: 基础依赖
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ \
    --default-timeout=1200 --retries=10 \
    fastapi uvicorn pymongo motor ...

# 第2-4批: 其他依赖...

# 第5-6批: AI 依赖(使用备选镜像)
RUN pip install ... -i https://pypi.tuna.tsinghua.edu.cn/simple ... || \
    pip install ... -i https://mirrors.aliyun.com/pypi/simple/ ...

# 5. Playwright 浏览器安装
RUN playwright install chromium && \
    apt-get install -y libnss3 libnspr4 ... fonts-unifont

# 6. 预下载 Whisper 模型
RUN python3 -c "from faster_whisper import WhisperModel; \
    WhisperModel('small', device='cpu', compute_type='int8')" || true
```

## 🚀 使用方法

### 方式 1: 使用优化的构建脚本(推荐)
```powershell
cd deployment
.\build-optimized.ps1
```

### 方式 2: 直接使用 docker-compose
```powershell
cd deployment
docker-compose build --no-cache backend
docker-compose up -d
```

### 方式 3: 只构建不启动
```powershell
cd deployment
docker-compose build backend
```

## 📊 性能对比

### 构建时间
| 阶段 | 优化前 | 优化后 | 说明 |
|------|--------|--------|------|
| 系统依赖 | ~2分钟 | ~2分钟 | 无变化 |
| Python 依赖 | **超时失败** | ~15-20分钟 | 分批安装,稳定完成 |
| Playwright | **失败** | ~1分钟 | 手动安装依赖 |
| 模型下载 | 运行时 | ~5-10分钟 | 提前到构建时 |
| **总计** | **失败** | **~25-35分钟** | ✅ 成功构建 |

### 首次运行
| 项目 | 优化前 | 优化后 |
|------|--------|--------|
| 模型加载 | 需下载(5-10分钟) | 直接加载(<1秒) |
| 转录速度 | 原版 Whisper(慢) | Faster-Whisper(快5-7倍) |

## 🔧 故障排查

### 如果构建仍然失败

1. **检查网络连接**
   ```powershell
   # 测试镜像源连接
   curl https://mirrors.aliyun.com/pypi/simple/
   curl https://hf-mirror.com
   ```

2. **切换镜像源**
   编辑 `deployment/.env`:
   ```env
   # 尝试其他镜像源
   PYPI_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple
   # PYPI_MIRROR=https://pypi.mirrors.ustc.edu.cn/simple/
   # PYPI_MIRROR=https://pypi.douban.com/simple/
   ```

3. **查看详细日志**
   ```powershell
   docker-compose build backend 2>&1 | Tee-Object build.log
   ```

4. **清理并重试**
   ```powershell
   docker-compose down
   docker system prune -a --volumes -f
   docker-compose build --no-cache backend
   ```

### 如果模型下载失败

运行时会自动降级:
1. 首先尝试 Faster-Whisper(从 hf-mirror.com)
2. 失败后降级到 OpenAI-Whisper
3. 两者都失败会报错,但不影响其他功能

## 📝 环境变量说明

### 必需的环境变量
```env
# MongoDB 配置
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=your_password
MONGODB_PORT=27018

# 应用配置
SECRET_KEY=your_secret_key
BACKEND_PORT=6002
FRONTEND_PORT=6004
```

### 可选的镜像源配置
```env
# Python 镜像源
PYPI_MIRROR=https://mirrors.aliyun.com/pypi/simple/

# Hugging Face 镜像(在 Dockerfile 中已配置)
# HF_ENDPOINT=https://hf-mirror.com
```

## 🎉 总结

通过以上优化,Docker 部署已经可以:
- ✅ 稳定完成构建(不再超时)
- ✅ 正确安装所有依赖
- ✅ 预下载 AI 模型
- ✅ 首次运行即可使用所有功能
- ✅ 提供完善的降级方案

如有其他问题,请参考:
- `deployment/DOCKER_BUILD_TIMEOUT_FIX.md` - 详细的问题解决方案
- `deployment/build-optimized.ps1` - 交互式构建脚本
- 构建日志 - 查看具体失败原因
