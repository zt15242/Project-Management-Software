# 部署检查清单

部署前请确认以下事项：

## 📋 服务器准备

- [ ] **服务器系统**: Linux (Ubuntu 20.04+, CentOS 7+, Debian 10+)
- [ ] **CPU**: 至少 2 核
- [ ] **内存**: 至少 4GB (推荐 8GB)
- [ ] **磁盘**: 至少 20GB 可用空间
- [ ] **网络**: 可访问互联网（用于下载 Docker 镜像）
- [ ] **权限**: 具有 sudo 权限的用户账号

## 🔧 软件要求

- [ ] Docker 已安装（版本 20.10.0+）
- [ ] Docker Compose 已安装（版本 1.29.0+）
- [ ] Git 已安装（可选，用于代码更新）

## 📁 项目文件

- [ ] 已上传完整项目文件到服务器
- [ ] `deployment` 目录包含所有必要文件:
  - [ ] docker-compose.yml
  - [ ] Dockerfile.backend
  - [ ] Dockerfile.frontend
  - [ ] .env.production
  - [ ] .dockerignore
  - [ ] deploy.sh
  - [ ] README.md

## 🔒 安全配置

- [ ] 已修改 `.env` 文件中的 `MONGO_INITDB_ROOT_PASSWORD`
- [ ] 已修改 `.env` 文件中的 `SECRET_KEY`（至少 32 字符）
- [ ] 已配置防火墙规则（开放端口 80, 8000）
- [ ] 生产环境考虑启用 HTTPS

## 🌐 网络配置

- [ ] 端口 80 未被占用（前端）
- [ ] 端口 8000 未被占用（后端 API）
- [ ] 端口 27017 未被占用（MongoDB）
- [ ] 防火墙已开放必要端口
- [ ] DNS 已配置（如果需要域名访问）

## 💾 数据备份

- [ ] 已准备数据备份目录
- [ ] 已了解备份命令: `./deploy.sh backup`
- [ ] 已制定定期备份计划

## 📝 部署步骤确认

1. [ ] 已阅读 `deployment/README.md`
2. [ ] 已配置 `.env` 文件
3. [ ] 已赋予 `deploy.sh` 执行权限: `chmod +x deploy.sh`
4. [ ] 准备执行构建: `./deploy.sh build`
5. [ ] 准备启动服务: `./deploy.sh start`

## ✅ 部署后验证

- [ ] 所有容器正常运行: `docker ps`
- [ ] 前端可访问: `http://服务器IP`
- [ ] 后端 API 可访问: `http://服务器IP:8000/docs`
- [ ] MongoDB 正常连接
- [ ] 可以注册和登录用户
- [ ] 可以创建项目和任务

## 🔍 监控和维护

- [ ] 已设置日志查看方式: `./deploy.sh logs`
- [ ] 已了解重启命令: `./deploy.sh restart`
- [ ] 已了解停止命令: `./deploy.sh stop`
- [ ] 已设置监控告警（可选）

## 📞 应急联系

- [ ] 已记录技术支持联系方式
- [ ] 已准备故障排查文档
- [ ] 已了解回滚步骤

---

**部署前请确保所有项目都已勾选！**

如有疑问，请查看详细文档: `deployment/README.md`
