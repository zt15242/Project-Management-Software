# Docker 部署文件总览

本目录包含了项目管理系统在 Linux 服务器上使用 Docker 部署的所有必要文件。

## 📁 文件清单

### 核心配置文件

| 文件名 | 说明 | 是否必需 |
|--------|------|----------|
| `docker-compose.yml` | Docker Compose 编排文件，定义所有服务 | ✅ 必需 |
| `Dockerfile.backend` | 后端 Docker 镜像构建文件 | ✅ 必需 |
| `Dockerfile.frontend` | 前端 Docker 镜像构建文件 | ✅ 必需 |
| `.env.production` | 生产环境配置模板 | ✅ 必需 |
| `.dockerignore` | Docker 构建忽略文件 | ✅ 必需 |

### 脚本文件

| 文件名 | 说明 | 用途 |
|--------|------|------|
| `deploy.sh` | 主部署脚本 | 构建、启动、停止、备份等所有操作 |
| `quick-deploy.sh` | 快速部署脚本 | 一键自动化部署（可选） |

### 文档文件

| 文件名 | 说明 | 建议阅读 |
|--------|------|----------|
| `README.md` | 完整部署指南 | ⭐⭐⭐⭐⭐ 必读 |
| `CHECKLIST.md` | 部署检查清单 | ⭐⭐⭐⭐ 部署前查看 |
| `FAQ.md` | 常见问题解答 | ⭐⭐⭐ 遇到问题时查看 |
| `INDEX.md` | 本文件，文件索引 | ⭐⭐ 快速了解 |

## 🚀 快速开始

### 最简部署流程（3 步）

```bash
# 1. 配置环境变量
cd deployment
cp .env.production .env
nano .env  # 修改密码和密钥

# 2. 授予执行权限并构建
chmod +x deploy.sh
./deploy.sh build

# 3. 启动服务
./deploy.sh start
```

### 访问系统

- 前端: http://服务器IP
- 后端 API: http://服务器IP:8000
- API 文档: http://服务器IP:8000/docs

## 📋 部署前准备

### 系统要求
- ✅ Linux 服务器（Ubuntu 20.04+, CentOS 7+）
- ✅ 2核 CPU + 4GB 内存 + 20GB 磁盘
- ✅ Docker 20.10+ 和 Docker Compose 1.29+

### 必须修改的配置
在 `.env` 文件中修改：
1. `MONGO_INITDB_ROOT_PASSWORD` - MongoDB 密码
2. `SECRET_KEY` - JWT 密钥（使用 `openssl rand -hex 32` 生成）

### 网络要求
开放以下端口：
- 80 (前端)
- 8000 (后端 API)
- 27017 (MongoDB，可选，如果需要外部访问)

## 🔧 常用命令

```bash
# 查看帮助
./deploy.sh help

# 服务管理
./deploy.sh build      # 构建镜像
./deploy.sh start      # 启动服务
./deploy.sh stop       # 停止服务
./deploy.sh restart    # 重启服务
./deploy.sh status     # 查看状态

# 日志查看
./deploy.sh logs              # 所有日志
./deploy.sh logs backend      # 后端日志
./deploy.sh logs frontend     # 前端日志

# 数据管理
./deploy.sh backup            # 备份数据库
./deploy.sh restore <file>    # 恢复数据库

# 清理（谨慎！）
./deploy.sh clean             # 清理所有资源
```

## 📊 服务架构

```
┌─────────────────────────────────────────┐
│            Nginx (前端)                  │
│         Port: 80                        │
│    静态文件 + API 反向代理                │
└──────────────┬──────────────────────────┘
               │
               │ API 请求
               ▼
┌─────────────────────────────────────────┐
│       FastAPI (后端)                     │
│         Port: 8000                      │
│     Python + Uvicorn                    │
└──────────────┬──────────────────────────┘
               │
               │ 数据操作
               ▼
┌─────────────────────────────────────────┐
│         MongoDB (数据库)                 │
│         Port: 27017                     │
│       数据持久化存储                      │
└─────────────────────────────────────────┘
```

## 🔄 持续化数据

Docker Volumes（数据不会因容器删除而丢失）：
- `mongodb_data` - 数据库数据
- `mongodb_config` - 数据库配置
- `backend_uploads` - 用户上传文件
- `backend_logs` - 应用日志

## ⚠️ 重要提示

1. **安全性**: 
   - ❌ 不要使用默认密码
   - ✅ 生产环境必须修改 `.env` 中的密码和密钥
   - ✅ 建议启用 HTTPS

2. **备份**: 
   - ✅ 定期备份数据: `./deploy.sh backup`
   - ✅ 备份文件保存在 `../backups/` 目录

3. **更新**: 
   - ✅ 更新前先备份
   - ✅ 更新后重新构建镜像

4. **监控**: 
   - ✅ 定期查看日志: `./deploy.sh logs`
   - ✅ 监控资源使用: `docker stats`

## 📖 文档阅读顺序

**首次部署建议阅读顺序:**

1. **INDEX.md** (本文件) - 快速了解 ⏱️ 5分钟
2. **CHECKLIST.md** - 部署前检查 ⏱️ 10分钟
3. **README.md** - 详细部署指南 ⏱️ 30分钟
4. **FAQ.md** - 常见问题（遇到问题时查看）

## 🆘 遇到问题？

1. 先查看 **FAQ.md**
2. 检查服务日志: `./deploy.sh logs`
3. 查看 **README.md** 的"故障排查"章节
4. 检查 Docker 容器状态: `docker ps`

## 📞 技术支持

- 📧 邮件: support@example.com (示例)
- 📚 文档: `deployment/README.md`
- 🐛 问题反馈: GitHub Issues (如果有仓库)

---

**版本**: 1.0.0  
**最后更新**: 2025-12-22  
**许可证**: MIT
