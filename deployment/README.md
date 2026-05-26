# 🚀 Docker 快速部署指南

## 一键构建命令

```powershell
# 进入部署目录
cd deployment

# 使用优化脚本构建(推荐)
.\build-optimized.ps1

# 或者直接使用 docker-compose
docker-compose build --no-cache backend
docker-compose up -d
```

## 已解决的问题 ✅

1. ✅ pip 依赖安装超时 → 分批安装 + 增加超时
2. ✅ Playwright 依赖失败 → 手动安装兼容包
3. ✅ Whisper 模型下载失败 → 国内镜像 + 预下载

## 构建时间预估

- **总时间**: 25-35 分钟
- **依赖安装**: 15-20 分钟
- **模型下载**: 5-10 分钟
- **其他**: 5 分钟

## 常用命令

```powershell
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 完全清理重建
docker-compose down
docker system prune -a --volumes -f
docker-compose build --no-cache
docker-compose up -d
```

## 访问地址

构建成功后:
- **前端**: http://localhost:6004
- **后端 API**: http://localhost:6002
- **API 文档**: http://localhost:6002/docs

## 故障排查

### 构建失败?
1. 检查网络连接
2. 查看 `deployment/DOCKER_BUILD_TIMEOUT_FIX.md`
3. 尝试切换镜像源(编辑 `.env` 文件)

### 模型下载失败?
不用担心!系统会自动降级:
- Faster-Whisper → OpenAI-Whisper
- 运行时会重试下载

### 需要帮助?
查看详细文档:
- `DOCKER_DEPLOYMENT_SUMMARY.md` - 完整解决方案
- `DOCKER_BUILD_TIMEOUT_FIX.md` - 问题详解
- `build-optimized.ps1` - 交互式构建

---
**提示**: 首次构建需要较长时间,请耐心等待。后续重建会利用缓存,速度更快。
