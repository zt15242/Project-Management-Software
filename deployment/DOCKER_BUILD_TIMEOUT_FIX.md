# Docker 构建超时问题解决方案

## 问题描述

构建过程中遇到两个主要问题:

### 1. pip 安装依赖时网络超时
- 从阿里云镜像下载大型包(594.3 MB)时,在下载到 363.4 MB 时超时
- 错误: `ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.`

### 2. Playwright 依赖安装失败
- 使用 `python:3.11-slim` 时,默认使用 Debian Trixie (testing)
- Playwright 的 `install-deps` 命令尝试安装已重命名的字体包
- 错误: `Package 'ttf-unifont' has no installation candidate`
- 原因: Debian Trixie 中 `ttf-unifont` 已改名为 `fonts-unifont`

## 已实施的优化方案

### 1. **分批安装依赖** ✅
将所有依赖包分为 6 个批次,避免单次下载过大:
- 第一批: 基础依赖(FastAPI, Uvicorn, MongoDB 等)
- 第二批: 文档处理依赖(Pillow, python-docx, openpyxl 等)
- 第三批: 网络请求依赖(httpx, requests)
- 第四批: 浏览器自动化依赖(playwright, selenium)
- 第五批: faster-whisper(最大的包,单独安装)
- 第六批: openai-whisper(备用方案)

### 2. **增加超时和重试配置** ✅
- 全局超时: `600秒` → `1200秒`
- 全局重试: `5次` → `10次`
- AI 依赖超时: `1800秒`(30分钟)
- AI 依赖重试: `15次`

### 3. **多镜像源备选** ✅
对于最大的包(whisper 相关),使用双重保险:
```dockerfile
RUN pip install ... -i https://pypi.tuna.tsinghua.edu.cn/simple ... || \
    pip install ... -i ${PYPI_MIRROR} ...
```
- 首选: 清华大学镜像
- 备选: 阿里云镜像

### 4. **手动安装 Playwright 依赖** ✅
不使用 `playwright install-deps`,而是手动安装必要的系统包:
- 使用 Debian Trixie 兼容的包名(如 `fonts-unifont` 替代 `ttf-unifont`)
- 只安装 Chromium 运行所需的核心依赖
- 避免安装不必要的包,减少构建时间

### 5. **预下载 Whisper 模型** ✅
在构建阶段预下载 AI 模型,避免首次使用时下载:
- 配置 `HF_ENDPOINT=https://hf-mirror.com` 使用国内镜像
- 预下载 Faster-Whisper small 模型
- 预下载 OpenAI-Whisper small 模型(备用)
- 即使下载失败也不影响构建,会在运行时重试

## 其他可选方案

### 方案 A: 使用 Docker BuildKit 缓存

在构建时启用 BuildKit 缓存:
```bash
# Windows PowerShell
$env:DOCKER_BUILDKIT=1
docker-compose build --no-cache backend
```

### 方案 B: 调整 Docker 网络设置

如果网络持续不稳定,可以尝试:
1. 修改 Docker Desktop 的 DNS 设置为 `8.8.8.8, 114.114.114.114`
2. 在 `docker-compose.yml` 中添加网络配置:
```yaml
services:
  backend:
    networks:
      - app-network
    dns:
      - 8.8.8.8
      - 114.114.114.114

networks:
  app-network:
    driver: bridge
```

### 方案 C: 预下载大型依赖

如果问题持续,可以考虑:
1. 在本地环境预先下载 wheel 文件
2. 将 wheel 文件复制到 Docker 镜像中
3. 使用 `pip install --no-index --find-links` 安装

示例:
```dockerfile
# 复制预下载的 wheel 文件
COPY ./wheels /tmp/wheels

# 从本地安装
RUN pip install --no-index --find-links=/tmp/wheels faster-whisper openai-whisper
```

### 方案 D: 使用多阶段构建

将依赖安装和应用构建分离:
```dockerfile
# 第一阶段: 安装依赖
FROM python:3.11-slim-bookworm AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 第二阶段: 复制依赖和应用
FROM python:3.11-slim-bookworm
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . .
```

### 方案 E: 切换到其他镜像源

如果阿里云镜像持续不稳定,可以尝试其他镜像:
- 清华大学: `https://pypi.tuna.tsinghua.edu.cn/simple`
- 中科大: `https://pypi.mirrors.ustc.edu.cn/simple/`
- 豆瓣: `https://pypi.douban.com/simple/`
- 华为云: `https://repo.huaweicloud.com/repository/pypi/simple`

修改 `.env` 文件:
```env
PYPI_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple
```

## 构建命令

### 重新构建(推荐)
```bash
# 清理旧镜像和缓存
docker-compose down
docker system prune -a --volumes

# 重新构建
docker-compose build --no-cache backend
docker-compose up -d
```

### 仅构建后端
```bash
docker-compose build backend
```

### 查看构建日志
```bash
docker-compose build backend 2>&1 | tee build.log
```

## 预期效果

1. **分批安装**: 每批下载量更小,超时风险降低
2. **更长超时**: 给予网络更多时间完成下载
3. **更多重试**: 临时网络波动时自动重试
4. **备选镜像**: 一个镜像失败时自动切换到另一个

## 监控建议

构建时关注以下信息:
- 每批依赖的下载时间
- 哪些包下载最慢
- 是否触发了备选镜像

如果问题仍然存在,可以考虑:
1. 检查网络连接质量
2. 尝试在网络较好的时间段构建
3. 考虑使用方案 C(预下载)或方案 E(切换镜像源)
