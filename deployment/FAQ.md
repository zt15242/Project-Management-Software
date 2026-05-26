# 常见问题解答 (FAQ)

## 📖 一般问题

### Q1: 最低服务器配置要求是什么？
**A**: 
- CPU: 2核
- 内存: 4GB (推荐 8GB)
- 磁盘: 20GB 可用空间
- 系统: Linux (Ubuntu 20.04+, CentOS 7+, Debian 10+)

### Q2: 是否支持 Windows 服务器部署？
**A**: 理论上可以，但强烈推荐使用 Linux 服务器。如果必须使用 Windows，建议使用 WSL2 + Docker Desktop。

### Q3: 部署需要多长时间？
**A**: 首次部署通常需要 15-40 分钟，具体取决于网络速度和服务器性能。后续更新部署一般 5-10 分钟。

---

## 🐳 Docker 相关

### Q4: Docker 镜像构建失败怎么办？
**A**: 
1. 检查网络连接
2. 使用国内镜像源（Dockerfile 中已配置）
3. 查看详细错误: `docker-compose build --no-cache`
4. 检查磁盘空间是否充足

### Q5: 如何更换 Docker 镜像源？
**A**: 
```bash
# 创建或编辑 /etc/docker/daemon.json
sudo nano /etc/docker/daemon.json

# 添加以下内容
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://registry.docker-cn.com"
  ]
}

# 重启 Docker
sudo systemctl restart docker
```

### Q6: 容器启动后自动停止怎么办？
**A**: 
1. 查看容器日志: `docker logs <container_id>`
2. 检查配置文件是否正确
3. 确认依赖服务（如 MongoDB）已启动
4. 检查端口是否被占用

---

## 🔧 配置问题

### Q7: 如何修改默认端口？
**A**: 编辑 `deployment/.env` 文件：
```env
BACKEND_PORT=8000    # 后端端口
FRONTEND_PORT=80     # 前端端口
MONGODB_PORT=27017   # 数据库端口
```
修改后重新启动: `./deploy.sh restart`

### Q8: 忘记 MongoDB 密码怎么办？
**A**: 
```bash
# 停止服务
./deploy.sh stop

# 修改 .env 文件中的密码
nano .env

# 清理数据卷（会删除数据！）
docker-compose down -v

# 重新启动
./deploy.sh start
```

### Q9: 如何生成安全的 SECRET_KEY？
**A**: 
```bash
# 使用 openssl
openssl rand -hex 32

# 或使用 Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🌐 网络问题

### Q10: 无法访问前端页面（端口 80）
**A**: 
1. 检查防火墙: `sudo ufw status`
2. 开放端口: `sudo ufw allow 80/tcp`
3. 检查容器状态: `docker ps`
4. 查看 Nginx 日志: `./deploy.sh logs frontend`

### Q11: API 请求 CORS 错误
**A**: 这通常是前端和后端不在同一域导致的。已在 `main.py` 中配置了 CORS，如果仍有问题，检查：
1. 后端是否正常运行
2. Nginx 配置是否正确
3. 浏览器控制台的具体错误信息

### Q12: 如何启用 HTTPS？
**A**: 
```bash
# 1. 安装 certbot
sudo apt-get install certbot

# 2. 获取 SSL 证书
sudo certbot certonly --standalone -d your-domain.com

# 3. 修改 nginx.conf 添加 SSL 配置
# 4. 更新 docker-compose.yml 挂载证书
# 5. 重启服务
```

---

## 💾 数据管理

### Q13: 如何备份数据？
**A**: 
```bash
# 使用部署脚本
./deploy.sh backup

# 备份文件位于 ../backups/ 目录
```

### Q14: 如何恢复数据？
**A**: 
```bash
./deploy.sh restore /path/to/backup.archive
```

### Q15: 数据存储在哪里？
**A**: 数据存储在 Docker volumes 中：
- `mongodb_data`: 数据库数据
- `backend_uploads`: 上传文件
- `backend_logs`: 日志文件

查看 volume 位置:
```bash
docker volume inspect deployment_mongodb_data
```

### Q16: 如何迁移到新服务器？
**A**: 
1. 在旧服务器备份: `./deploy.sh backup`
2. 复制项目文件和备份文件到新服务器
3. 在新服务器部署: `./deploy.sh build && ./deploy.sh start`
4. 恢复数据: `./deploy.sh restore backup.archive`

---

## 🔍 性能优化

### Q17: 系统运行缓慢怎么办？
**A**: 
1. 检查资源使用: `docker stats`
2. 增加服务器内存
3. 为 MongoDB 创建索引
4. 启用 Nginx 缓存（已配置）
5. 限制容器资源（在 docker-compose.yml 中配置）

### Q18: 磁盘空间不足
**A**: 
```bash
# 清理未使用的 Docker 资源
docker system prune -a

# 清理旧日志
find backend/logs -name "*.log" -mtime +30 -delete
```

---

## 🐛 故障排查

### Q19: 如何查看日志？
**A**: 
```bash
# 查看所有服务日志
./deploy.sh logs

# 查看特定服务
./deploy.sh logs backend
./deploy.sh logs frontend
./deploy.sh logs mongodb

# 实时查看
docker-compose logs -f backend
```

### Q20: MongoDB 连接失败
**A**: 
1. 检查 MongoDB 容器状态: `docker ps | grep mongodb`
2. 查看 MongoDB 日志: `./deploy.sh logs mongodb`
3. 测试连接: 
```bash
docker-compose exec mongodb mongosh \
  --username admin \
  --password your_password \
  --eval "db.runCommand({ping:1})"
```

### Q21: 容器内存溢出 (OOM)
**A**: 
在 `docker-compose.yml` 中添加内存限制：
```yaml
services:
  backend:
    mem_limit: 1g
    mem_reservation: 512m
```

---

## 🔄 更新和维护

### Q22: 如何更新应用？
**A**: 
```bash
# 1. 备份数据
./deploy.sh backup

# 2. 停止服务
./deploy.sh stop

# 3. 更新代码（git pull 或重新上传）
git pull

# 4. 重新构建
./deploy.sh build

# 5. 启动服务
./deploy.sh start
```

### Q23: 如何回滚到之前版本？
**A**: 
```bash
# 如果使用 Git
git checkout <previous-commit>
./deploy.sh build
./deploy.sh start

# 恢复数据
./deploy.sh restore backup.archive
```

### Q24: 多久需要重启一次服务？
**A**: 正常情况下不需要定期重启。只在以下情况需要重启：
- 更新配置
- 更新代码
- 系统维护
- 出现异常

---

## 🔐 安全问题

### Q25: 如何加强安全性？
**A**: 
1. 修改所有默认密码
2. 使用强密钥（至少 32 字符）
3. 启用 HTTPS
4. 配置防火墙，只开放必要端口
5. 定期更新系统和 Docker
6. 定期备份数据
7. 使用 IP 白名单（如果可能）
8. 关闭不必要的服务

### Q26: 如何查看谁在访问系统？
**A**: 
```bash
# 查看 Nginx 访问日志
./deploy.sh logs frontend | grep "GET\|POST"

# 查看后端日志
./deploy.sh logs backend
```

---

## 💡 开发相关

### Q27: 如何在容器内调试？
**A**: 
```bash
# 进入后端容器
docker-compose exec backend bash

# 进入 MongoDB
docker-compose exec mongodb mongosh
```

### Q28: 如何添加新的 Python 依赖？
**A**: 
1. 修改 `backend/requirements.txt`
2. 重新构建镜像: `./deploy.sh build`
3. 重启服务: `./deploy.sh restart`

---

## 📞 获取帮助

### Q29: 遇到问题找不到解决方案怎么办？
**A**: 
1. 查看完整文档: `deployment/README.md`
2. 检查容器日志: `./deploy.sh logs`
3. 搜索 Docker Hub 上的相关问题
4. 查看 FastAPI/Vue.js 官方文档
5. 联系技术支持

### Q30: 如何贡献或报告 bug？
**A**: 
1. 提交 GitHub Issue（如果有仓库）
2. 提供详细的错误信息和日志
3. 说明环境配置（系统、Docker版本等）
4. 描述复现步骤

---

**持续更新中... 如有其他问题，请联系技术支持。**
