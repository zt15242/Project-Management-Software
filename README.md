# 项目管理系统

一个功能完善的企业级项目管理系统，集成了项目管理、任务跟踪、课题管理、代码发布、BI报表、AI助手等多个模块。

## 主要功能

### 基础管理
- 👥 **用户管理**: 支持多角色（管理员、项目经理、开发、测试、外部人员）
- 📁 **项目管理**: 项目创建、团队管理、权限控制
- ✅ **任务管理**: 任务分配、状态跟踪、优先级管理
- 🐛 **课题管理**: 课题创建、流转、复测、关闭（支持分页搜索、邮件提醒）
- 📊 **数据看板**: 项目统计、任务分析、可视化报表

### 高级功能
- 🚀 **代码发布**: 版本管理、AI代码分析、自动部署（支持强制覆盖）
- 📈 **BI报表**: 数据源管理、报表设计、仪表板
- 🤖 **AI集成**: 
  - 代码质量分析（支持多种AI平台）
  - 会议语音转录（Whisper + 阿里云DashScope）
  - PPT自动生成（LandPPT引擎）
- 📚 **知识库**: 文档管理、全文搜索、权限控制
- 📧 **邮件提醒**: 课题分配、任务通知自动发送邮件
- 🔄 **环境管理**: 自动刷新登录状态（每2小时）

## 技术栈

### 前端
- Vue 3.3.8 + Vite 5
- Element Plus 2.4
- Pinia 状态管理
- ECharts 数据可视化
- Axios HTTP 客户端

### 后端
- FastAPI + Uvicorn
- MongoDB (Motor 异步驱动)
- JWT 认证
- APScheduler 定时任务
- Selenium 自动化登录

### AI 能力
- OpenAI GPT / 通义千问 / 智谱AI / Claude / DeepSeek / Gemini
- Whisper 语音识别
- 阿里云 DashScope ASR
- LandPPT 引擎

### 部署
- Docker + Docker Compose
- Nginx 反向代理

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 16+
- MongoDB 6.0+
- Docker & Docker Compose（可选）

### 本地开发

#### 1. 克隆项目
```bash
git clone https://github.com/zt15242/Project-Management-Software.git
cd Project-Management-Software
```

#### 2. 后端启动
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt

# 复制配置文件
cp .env.example .env
# 编辑 .env 配置数据库等信息

# 启动服务
python main.py
```

后端服务运行在 http://localhost:8000
API 文档: http://localhost:8000/docs

#### 3. 前端启动
```bash
cd frontend
npm install
npm run dev
```

前端服务运行在 http://localhost:3000

### Docker 部署

#### 1. 准备配置文件
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置（重要！）
nano .env
```

修改以下配置：
```bash
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=project_management_prod
SECRET_KEY=生成一个随机的长字符串
FRONTEND_URL=https://your-domain.com
```

#### 2. 创建端口覆盖配置（可选）
```bash
nano docker-compose.override.yml
```

```yaml
version: '3.8'
services:
  backend:
    ports:
      - "6002:8000"  # 自定义端口
  frontend:
    ports:
      - "6004:80"
```

#### 3. 启动服务
```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

访问地址：
- 前端: http://localhost:6004
- 后端: http://localhost:6002
- API文档: http://localhost:6002/docs

## 自动部署（推荐）

项目支持 Git + Webhook 自动部署，详见 [环境自动刷新功能说明](docs/环境自动刷新功能说明.md)

### 部署脚本
```bash
# 首次部署
./deployment/deploy.sh

# 回滚到指定版本
./deployment/rollback.sh v1.0.0
```

## 项目结构

```
Project-Management-Software/
├── backend/                 # 后端服务
│   ├── main.py             # 应用入口
│   ├── config.py           # 配置管理
│   ├── models.py           # 数据模型
│   ├── routers/            # API路由
│   ├── services/           # 业务服务
│   │   ├── ai/            # AI服务
│   │   ├── email_service.py
│   │   └── environment_refresh_service.py
│   └── requirements.txt
│
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 公共组件
│   │   ├── api/           # API封装
│   │   ├── stores/        # Pinia状态
│   │   └── router/        # 路由配置
│   └── package.json
│
├── deployment/             # 部署脚本
│   ├── deploy.sh          # 自动部署
│   ├── rollback.sh        # 版本回滚
│   ├── backup.sh          # 数据备份
│   └── docker-compose.yml
│
├── docs/                   # 项目文档
│   ├── README.md
│   ├── API接口文档.md
│   └── 环境自动刷新功能说明.md
│
├── .env.example           # 环境变量模板
├── .gitignore
└── README.md
```

## 核心功能说明

### 课题管理
- 支持分页、搜索（关键词、状态、负责人、严重度）
- 创建课题时自动发送邮件提醒负责人
- 邮件中课题号可点击跳转详情页
- 完整的流转流程：创建 → 分配 → 处理 → 复测 → 关闭

### 代码发布
- AI自动分析代码质量（支持多种AI平台）
- 基于NEO开发规范的静态检查
- 自动部署到远程环境
- 支持强制覆盖部署（处理 code 290052 冲突）
- 版本对比和回滚

### 环境管理
- 自动刷新登录状态（每2小时）
- 防止 Cookie 失效
- 支持手动触发刷新
- 详细的刷新日志

## 配置说明

### 环境变量
主要配置项（`.env` 文件）：

```bash
# 数据库
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=project_management

# 服务器
HOST=0.0.0.0
PORT=8000
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# JWT
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI配置（可选）
DASHSCOPE_API_KEY=your-dashscope-key
GEMINI_IMAGE_API_KEY=your-gemini-key

# OSS配置（可选）
OSS_PROVIDER=aliyun
OSS_ACCESS_KEY_ID=your-access-key
OSS_ACCESS_KEY_SECRET=your-secret-key
OSS_BUCKET_NAME=your-bucket
```

### 端口配置
- 开发环境：前端 3000，后端 8000
- 生产环境：可通过 `docker-compose.override.yml` 自定义

## 数据备份

### 自动备份
```bash
# 添加到 crontab（每天凌晨2点）
0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1
```

### 手动备份
```bash
# 备份 MongoDB
docker exec mongodb mongodump --out /tmp/backup
docker cp mongodb:/tmp/backup ./backup_$(date +%Y%m%d)

# 备份上传文件
tar -czf uploads_backup.tar.gz backend/uploads/
```

## 常见问题

### 1. MongoDB 连接失败
检查 MongoDB 是否启动：
```bash
docker-compose ps
# 或
systemctl status mongod
```

### 2. 前端无法访问后端
检查 CORS 配置和代理设置（`frontend/vite.config.js`）

### 3. 邮件发送失败
检查邮箱配置是否正确（系统管理 → 邮箱配置）

### 4. 环境自动刷新不工作
检查后端日志，确认定时任务是否启动

## 开发规范

- 后端遵循 FastAPI 最佳实践
- 前端遵循 Vue 3 Composition API 规范
- 代码提交前运行测试和 lint
- 使用语义化版本号（Semantic Versioning）

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证

## 联系方式

- 项目地址: https://github.com/zt15242/Project-Management-Software
- 问题反馈: https://github.com/zt15242/Project-Management-Software/issues

## 更新日志

### v1.0.0 (2026-05-26)
- ✨ 课题管理增加分页和搜索功能
- ✨ 课题创建时自动发送邮件提醒
- ✨ 代码部署支持强制覆盖（处理 290052 冲突）
- ✨ 环境配置自动刷新登录状态（每2小时）
- 🐛 修复部署接口的各种边界情况
- 📝 完善项目文档和部署说明
