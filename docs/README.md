# 项目管理系统

一个功能完善的项目管理系统，支持项目、任务、BUG管理以及数据统计看板。

## 技术栈

### 后端
- **Python 3.9+**
- **FastAPI** - 现代、快速的 Web 框架
- **MongoDB** - NoSQL 数据库
- **Motor** - MongoDB 异步驱动
- **JWT** - 用户认证
- **Pydantic** - 数据验证

### 前端
- **Vue 3** - 渐进式 JavaScript 框架
- **Element Plus** - Vue 3 UI 组件库
- **Pinia** - Vue 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP 客户端
- **ECharts** - 数据可视化

## 主要功能

### 1. 用户管理
- 用户注册和登录
- 多角色支持（管理员、项目经理、开发人员、测试人员）
- 用户权限控制

### 2. 项目管理
- 创建和管理项目
- 项目团队成员管理
- 项目信息编辑
- 项目状态跟踪

### 3. 任务管理
- 创建和分配任务
- 任务状态管理（待办、进行中、已完成、已取消）
- 任务优先级设置（低、中、高、紧急）
- 任务工时统计
- 任务筛选和查询

### 4. BUG管理
- 创建和分配BUG
- BUG状态流转（打开、已分配、处理中、已修复、测试中、已关闭、重新打开）
- BUG严重程度分级（低、中、高、严重）
- BUG附件上传（支持图片）
- BUG复测流程
- 复测通过关闭BUG
- 复测失败重新打开BUG

### 5. 通知系统
- 实时通知推送
- BUG分配通知
- Windows桌面通知
- 通知中心查看
- 未读通知提醒

### 6. 数据看板
- 项目统计概览
- 任务完成率统计
- BUG率统计
- 团队成员统计
- 可视化图表展示

## 安装和运行

### 环境要求
- Python 3.9+
- Node.js 16+
- MongoDB 4.4+

### 后端安装

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动MongoDB（确保MongoDB服务已启动）

# 运行后端服务
python main.py
```

后端服务将在 `http://localhost:8000` 启动。

API文档地址：`http://localhost:8000/docs`

### 前端安装

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:3000` 启动。

### 生产环境部署

#### 后端部署

```bash
cd backend

# 使用 gunicorn 或 uvicorn 部署
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 前端部署

```bash
cd frontend

# 构建生产版本
npm run build

# dist 目录包含构建后的文件，可以部署到任何静态文件服务器
```

## 配置说明

### 后端配置

在 `backend` 目录下创建 `.env` 文件：

```env
# MongoDB配置
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=project_management

# JWT配置
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 文件上传配置
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE=10485760

# 服务器配置
HOST=0.0.0.0
PORT=8000
```

### 前端配置

修改 `frontend/vite.config.js` 中的后端API地址（如果需要）。

## 默认账号

首次使用需要先注册账号。建议创建以下类型的账号进行测试：

1. 管理员账号（用于用户管理）
2. 项目经理账号（用于项目管理）
3. 开发人员账号（用于任务和BUG处理）
4. 测试人员账号（用于BUG复测）

## 使用流程

1. **注册登录**
   - 访问 `http://localhost:3000`
   - 注册账号并登录

2. **创建项目**
   - 进入"项目"页面
   - 点击"创建项目"按钮
   - 填写项目信息

3. **添加团队成员**
   - 在项目列表中点击"成员"按钮
   - 选择用户添加到项目团队

4. **创建任务**
   - 进入"任务"页面
   - 点击"创建任务"按钮
   - 选择项目、分配负责人、设置优先级等

5. **创建BUG**
   - 进入"BUG"页面
   - 点击"创建BUG"按钮
   - 填写BUG信息、选择项目、分配负责人

6. **BUG处理流程**
   - 开发人员修复BUG，更新状态为"已修复"，填写修复说明
   - 测试人员进行复测
   - 复测通过：关闭BUG
   - 复测失败：重新打开BUG

7. **查看数据看板**
   - 进入"控制台"页面
   - 查看项目统计、任务完成率、BUG率等数据

## 通知功能

系统支持Windows桌面通知功能：

- 当BUG被分配时，会发送通知
- 当BUG被关闭或重新打开时，会发送通知
- 浏览器会请求通知权限，请允许以接收桌面通知

## API文档

后端提供了完整的API文档，启动后端服务后访问：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 目录结构

```
项目管理软件2/
├── backend/                 # 后端代码
│   ├── routers/            # API路由
│   │   ├── auth.py         # 认证相关
│   │   ├── users.py        # 用户管理
│   │   ├── projects.py     # 项目管理
│   │   ├── tasks.py        # 任务管理
│   │   ├── bugs.py         # BUG管理
│   │   ├── statistics.py   # 统计数据
│   │   └── notifications.py # 通知管理
│   ├── main.py             # 主应用
│   ├── config.py           # 配置文件
│   ├── database.py         # 数据库连接
│   ├── models.py           # 数据模型
│   ├── auth.py             # 认证逻辑
│   └── requirements.txt    # Python依赖
│
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── api/           # API调用
│   │   ├── layouts/       # 布局组件
│   │   ├── router/        # 路由配置
│   │   ├── stores/        # 状态管理
│   │   ├── views/         # 页面组件
│   │   ├── App.vue        # 根组件
│   │   └── main.js        # 入口文件
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
└── README.md              # 项目文档
```

## 常见问题

### 1. MongoDB连接失败
确保MongoDB服务已启动，检查配置文件中的连接地址是否正确。

### 2. 前端无法连接后端
检查后端是否正常运行，查看浏览器控制台的错误信息。

### 3. 图片上传失败
确保后端的 `uploads` 目录存在且有写入权限。

### 4. 桌面通知不显示
检查浏览器通知权限是否已允许。

## 开发计划

- [ ] 添加任务评论功能
- [ ] 添加项目进度甘特图
- [ ] 添加邮件通知
- [ ] 添加移动端适配
- [ ] 添加导出报表功能
- [ ] 添加文件附件管理
- [ ] 添加实时协作功能

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎提交Issue。

