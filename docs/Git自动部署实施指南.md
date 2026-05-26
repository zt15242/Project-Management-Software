# Git 自动部署方案 - Windows Server 实施指南

## 方案概述

通过 Git + Webhook 实现自动部署：
- 推送代码到 GitHub → 自动触发部署
- 自动备份 → 健康检查 → 失败自动回滚
- 零停机时间（后端代码通过 bind mount 挂载）

## 前置条件

- ✅ Windows Server
- ✅ Git 已安装
- ✅ Docker Desktop 已安装并运行
- ✅ 服务器有公网 IP
- ✅ 代码已推送到 GitHub

## 实施步骤

### 阶段 1：迁移到 Git 部署（一次性操作）

#### 1.1 测试模式迁移（推荐，安全）

在新目录测试，不影响现有服务：

```powershell
# 在服务器上执行
cd D:\

# 下载迁移脚本（如果还没有 git 仓库）
git clone https://github.com/zt15242/Project-Management-Software.git temp-repo
cd temp-repo\deployment

# 执行测试迁移（使用不同端口 6012/6014）
.\migrate-to-git.ps1 `
    -OldDir "D:\Project_Package_20260304_1520" `
    -NewDir "D:\project-git" `
    -TestMode

# 测试新部署
# 后端: http://localhost:6012/health
# 前端: http://localhost:6014
```

**测试通过后，执行完全迁移：**

```powershell
# 停止测试服务
cd D:\project-git\deployment
docker-compose down

# 执行完全迁移（会停止旧服务）
cd D:\temp-repo\deployment
.\migrate-to-git.ps1 `
    -OldDir "D:\Project_Package_20260304_1520" `
    -NewDir "D:\project-git"

# 验证服务
# 后端: http://localhost:6002/health
# 前端: http://localhost:6004
```

#### 1.2 直接迁移（快速但有风险）

如果你对配置很有信心，可以直接迁移：

```powershell
cd D:\
git clone https://github.com/zt15242/Project-Management-Software.git temp-repo
cd temp-repo\deployment

.\migrate-to-git.ps1 `
    -OldDir "D:\Project_Package_20260304_1520" `
    -NewDir "D:\project-git"
```

#### 1.3 迁移后检查

```powershell
# 检查容器状态
docker ps

# 检查后端健康
curl http://localhost:6002/health

# 检查前端
curl http://localhost:6004

# 查看日志
cd D:\project-git\deployment
docker-compose logs -f backend
```

---

### 阶段 2：配置自动部署

#### 2.1 启动 Webhook 接收器

```powershell
# 进入项目目录
cd D:\project-git\deployment

# 启动 webhook 服务（前台运行，测试用）
.\webhook-server.ps1 `
    -Port 9000 `
    -DeployScript "D:\project-git\deployment\deploy.ps1" `
    -AllowedBranch "main"

# 测试健康检查
curl http://localhost:9000/health
```

**输出示例：**
```
============================================================
GitHub Webhook 接收器启动中...
  监听端口: 9000
  部署脚本: D:\project-git\deployment\deploy.ps1
  允许分支: main
  Secret: 未配置（不验证签名）
============================================================

[INFO] 监听器已启动: http://localhost:9000/webhook/
[INFO] 等待 GitHub Webhook 请求...
```

#### 2.2 配置为 Windows 服务（后台运行）

**方法 1：使用 NSSM（推荐）**

```powershell
# 下载 NSSM: https://nssm.cc/download
# 解压到 C:\nssm\

# 安装服务
C:\nssm\nssm.exe install GitWebhook `
    "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" `
    "-ExecutionPolicy Bypass -File D:\project-git\deployment\webhook-server.ps1 -Port 9000 -DeployScript D:\project-git\deployment\deploy.ps1"

# 启动服务
net start GitWebhook

# 查看服务状态
sc query GitWebhook
```

**方法 2：使用任务计划程序**

```powershell
# 创建启动时运行的任务
$Action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File D:\project-git\deployment\webhook-server.ps1 -Port 9000 -DeployScript D:\project-git\deployment\deploy.ps1"

$Trigger = New-ScheduledTaskTrigger -AtStartup

$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "GitWebhook" -Action $Action -Trigger $Trigger -Principal $Principal

# 立即启动
Start-ScheduledTask -TaskName "GitWebhook"
```

#### 2.3 配置防火墙

```powershell
# 允许 9000 端口入站
New-NetFirewallRule -DisplayName "Git Webhook" `
    -Direction Inbound `
    -LocalPort 9000 `
    -Protocol TCP `
    -Action Allow
```

#### 2.4 配置 GitHub Webhook

1. 访问 GitHub 仓库：https://github.com/zt15242/Project-Management-Software
2. 点击 **Settings** → **Webhooks** → **Add webhook**
3. 配置：
   - **Payload URL**: `http://你的服务器IP:9000/webhook`
   - **Content type**: `application/json`
   - **Secret**: 留空（或设置一个密钥，需同步修改 webhook-server.ps1 的 -Secret 参数）
   - **Which events**: 选择 `Just the push event`
   - **Active**: ✅ 勾选
4. 点击 **Add webhook**

#### 2.5 测试自动部署

```powershell
# 在本地修改代码并推送
cd "D:\销售易项目\项目管理软件2"
echo "# Test" >> README.md
git add README.md
git commit -m "Test auto deploy"
git push origin main

# 观察服务器上的 webhook 接收器日志
# 应该会看到：
# [2026-05-26 14:00:00] 收到请求: POST /webhook from xxx.xxx.xxx.xxx
# [DEPLOY] 启动部署脚本...
```

---

### 阶段 3：日常使用

#### 3.1 自动部署流程

```
本地修改代码
    ↓
git push origin main
    ↓
GitHub 触发 Webhook
    ↓
服务器接收 Webhook
    ↓
自动执行 deploy.ps1
    ↓
备份 → 拉代码 → 构建 → 重启 → 健康检查
    ↓
成功 ✓ 或 失败自动回滚 ✗
```

#### 3.2 手动部署

```powershell
cd D:\project-git\deployment
.\deploy.ps1
```

**可选参数：**
```powershell
# 指定分支
.\deploy.ps1 -Branch "develop"

# 跳过备份（快速部署）
.\deploy.ps1 -SkipBackup

# 跳过前端构建（只改了后端代码）
.\deploy.ps1 -SkipFrontendBuild
```

#### 3.3 查看部署日志

```powershell
# 日志位置
cd D:\project-git\..\\_deploy_logs

# 查看最新日志
Get-ChildItem | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content
```

#### 3.4 回滚

**查看可用版本：**
```powershell
cd D:\project-git\deployment
.\rollback.ps1 -List
```

**按 commit 回滚：**
```powershell
.\rollback.ps1 -Commit abc1234
```

**按备份时间回滚：**
```powershell
.\rollback.ps1 -BackupTimestamp 20260526_140000
```

---

## 目录结构

```
D:\project-git\                    # Git 仓库根目录
├── backend\
│   ├── .env                       # 环境变量（不提交到 Git）
│   └── ...
├── deployment\
│   ├── docker-compose.yml         # 基础配置（Git 管理）
│   ├── docker-compose.override.yml # 端口覆盖（不提交到 Git）
│   ├── deploy.ps1                 # 自动部署脚本
│   ├── webhook-server.ps1         # Webhook 接收器
│   ├── migrate-to-git.ps1         # 迁移脚本
│   ├── rollback.ps1               # 回滚脚本
│   └── data\
│       ├── uploads\               # 用户上传文件（持久化）
│       └── logs\                  # 日志（持久化）
├── frontend\
│   └── ...
└── .git\

D:\_deploy_backups\                # 备份目录（Git 外）
├── backup_20260526_140000\
│   ├── commit.txt
│   ├── .env
│   └── mongodb\
└── ...

D:\_deploy_logs\                   # 部署日志（Git 外）
├── deploy_20260526_140000.log
└── ...
```

---

## 常见问题

### 1. Webhook 接收器启动失败

**错误**：`启动失败: 拒绝访问`

**解决**：以管理员身份运行，或执行：
```powershell
netsh http add urlacl url=http://+:9000/ user=Everyone
```

### 2. GitHub Webhook 显示失败

**检查**：
- 服务器防火墙是否开放 9000 端口
- 公网 IP 是否正确
- Webhook 接收器是否在运行：`curl http://localhost:9000/health`

### 3. 部署后服务不健康

**查看日志**：
```powershell
cd D:\project-git\deployment
docker-compose logs backend
docker-compose logs frontend
```

**常见原因**：
- `.env` 文件配置错误
- MongoDB 连接失败
- 端口被占用

### 4. 前端更新不生效

前端代码打包进镜像，需要重新构建：
```powershell
cd D:\project-git\deployment
docker-compose build frontend
docker-compose up -d
```

### 5. 后端代码更新不生效

后端代码通过 bind mount 挂载，只需重启容器：
```powershell
cd D:\project-git\deployment
docker-compose restart backend
```

### 6. 如何回到旧的部署方式

```powershell
# 停止新部署
cd D:\project-git\deployment
docker-compose down

# 启动旧部署
cd D:\Project_Package_20260304_1520\deployment
docker-compose up -d
```

---

## 安全建议

### 1. 配置 Webhook Secret

```powershell
# 生成随机密钥
$Secret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
Write-Host $Secret

# 启动 webhook 时使用
.\webhook-server.ps1 -Port 9000 -Secret $Secret -DeployScript "D:\project-git\deployment\deploy.ps1"

# 在 GitHub Webhook 配置中填入相同的 Secret
```

### 2. 限制访问 IP

```powershell
# 只允许 GitHub IP 访问 9000 端口
# GitHub Webhook IP 范围: https://api.github.com/meta

New-NetFirewallRule -DisplayName "Git Webhook - GitHub Only" `
    -Direction Inbound `
    -LocalPort 9000 `
    -Protocol TCP `
    -Action Allow `
    -RemoteAddress "140.82.112.0/20", "143.55.64.0/20"
```

### 3. 定期备份

```powershell
# 创建定时任务，每天凌晨 2 点备份 MongoDB
$Action = New-ScheduledTaskAction -Execute "docker" `
    -Argument "exec mongo-1 mongodump --out /tmp/backup_$(Get-Date -Format 'yyyyMMdd')"

$Trigger = New-ScheduledTaskTrigger -Daily -At 2am

Register-ScheduledTask -TaskName "MongoDBBackup" -Action $Action -Trigger $Trigger
```

---

## 性能优化

### 1. 跳过不必要的构建

如果只改了后端 Python 代码（不是 requirements.txt），可以跳过镜像构建：
```powershell
.\deploy.ps1 -SkipFrontendBuild
```

### 2. 清理旧备份

备份会自动保留 30 天，手动清理：
```powershell
Get-ChildItem D:\_deploy_backups -Directory -Filter "backup_*" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } |
    Remove-Item -Recurse -Force
```

### 3. 清理 Docker 镜像

```powershell
# 清理无标签镜像
docker image prune -f

# 清理旧的备份镜像（保留最近 5 个）
docker images --format "{{.Repository}}:{{.Tag}}" |
    Select-String "backup_" |
    Select-Object -Skip 5 |
    ForEach-Object { docker rmi $_ }
```

---

## 总结

✅ **已实现**：
- Git 版本管理
- 推送代码自动部署
- 自动备份和回滚
- 健康检查
- 部署日志

✅ **优势**：
- 一劳永逸，推送即部署
- 失败自动回滚，安全可靠
- 完整的备份机制
- 支持手动回滚到任意版本

✅ **维护成本**：
- 日常：零维护（自动部署）
- 偶尔：查看日志、清理备份

有问题请查看部署日志或 GitHub Issues。
