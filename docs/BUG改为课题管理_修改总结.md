# BUG管理改为课题管理 - 修改总结

## 修改日期
2026-01-26

## 修改内容

### 1. 后端修改

#### 1.1 数据模型 (`backend/models.py`)
- 将 `BugStatus` 改为 `TopicStatus`
- 将 `BugSeverity` 改为 `TopicSeverity`
- 将 `BugCreate`, `BugUpdate`, `BugResponse` 改为 `TopicCreate`, `TopicUpdate`, `TopicResponse`
- 将 `BugCommentCreate`, `BugCommentResponse` 改为 `TopicCommentCreate`, `TopicCommentResponse`
- **新增字段**: `TopicResponse` 中添加 `topic_number` 字段（课题号）
- 将 `bug_images` 改为 `topic_images`
- 更新统计模型中的字段名（`total_bugs` → `total_topics` 等）
- 更新日报模型中的字段名（`bug_id` → `topic_id`, `bug_title` → `topic_title`）

#### 1.2 路由文件
- **新建**: `backend/routers/topics.py`（替代 `bugs.py`）
- **核心功能**: 实现课题号自动生成逻辑
  - 格式: `DB + 年月日 + 序列号`
  - 示例: `DB20260126001`, `DB20260126002`, ..., `DB202601261000`
  - 序列号至少3位，不足补0，支持自动扩展到4位、5位等
- 更新 `backend/main.py` 中的路由注册（`bugs` → `topics`）
- 更新 `backend/routers/daily_reports.py` 中的相关字段
- 更新 `backend/routers/notifications.py` 中的相关字段

### 2. 前端修改

#### 2.1 API接口 (`frontend/src/api/index.js`)
- 将 `bugAPI` 改为 `topicAPI`
- 更新所有API端点（`/bugs/` → `/topics/`）
- 更新方法名（`getBugs` → `getTopics`, `createBug` → `createTopic` 等）

#### 2.2 视图组件
- **新建**: `frontend/src/views/Topics.vue`（替代 `Bugs.vue`）
- **新建**: `frontend/src/views/TopicDetail.vue`（替代 `BugDetail.vue`）
- **新增功能**: 在表格中显示课题号列（`topic_number`）
- 更新所有文本标签（"BUG" → "课题"）
- 更新所有变量名和函数名

#### 2.3 路由配置 (`frontend/src/router/index.js`)
- 将 `/bugs` 路由改为 `/topics`
- 将 `/bugs/:id` 路由改为 `/topics/:id`
- 更新组件引用

#### 2.4 布局组件 (`frontend/src/layouts/MainLayout.vue`)
- 更新侧边栏菜单项（"BUG" → "课题"）
- 更新通知跳转逻辑（`bug_id` → `topic_id`）

### 3. 数据库字段变更

#### 3.1 集合名称
- `bugs` → `topics`
- `bug_comments` → `topic_comments`

#### 3.2 字段名称
- `bug_images` → `topic_images`
- `bug_id` → `topic_id`
- `bug_title` → `topic_title`
- **新增**: `topic_number`（课题号，自动生成）

### 4. 课题号生成规则

#### 4.1 格式说明
```
DB + YYYYMMDD + XXX
```
- `DB`: 固定前缀
- `YYYYMMDD`: 年月日（8位）
- `XXX`: 序列号（至少3位，不足补0）

#### 4.2 生成逻辑
1. 获取当前日期（北京时间）
2. 查询当天已有的最大序列号
3. 序列号+1
4. 格式化为至少3位数字
5. 拼接生成完整课题号

#### 4.3 示例
- 第1个: `DB20260126001`
- 第2个: `DB20260126002`
- ...
- 第999个: `DB20260126999`
- 第1000个: `DB202601261000`
- 第10000个: `DB2026012610000`

### 5. 兼容性说明

#### 5.1 数据迁移
如果已有BUG数据，需要执行以下操作：
1. 重命名集合：`bugs` → `topics`
2. 重命名集合：`bug_comments` → `topic_comments`
3. 为所有现有课题生成课题号
4. 更新所有引用字段名

#### 5.2 通知系统
- 通知中的 `bug_id` 字段已改为 `topic_id`
- 通知类型保持不变，但显示文本已更新

### 6. 测试建议

1. **创建课题**: 验证课题号自动生成
2. **跨天测试**: 验证不同日期的序列号独立计数
3. **大量创建**: 验证序列号自动扩展（超过999）
4. **编辑课题**: 验证课题号不变
5. **删除课题**: 验证序列号不回收（保持递增）
6. **通知跳转**: 验证课题相关通知正确跳转
7. **日报关联**: 验证日报可正确关联课题

### 7. 注意事项

1. 课题号一旦生成不可修改
2. 删除课题后，其课题号不会被重新使用
3. 序列号按天独立计数，每天从001开始
4. 系统时间使用北京时间（UTC+8）
5. 前端需要重新编译才能生效
6. 后端需要重启服务才能生效

## 文件清单

### 后端文件
- `backend/models.py` - 数据模型定义
- `backend/routers/topics.py` - 课题管理路由（新建）
- `backend/main.py` - 主应用配置
- `backend/routers/daily_reports.py` - 日报管理
- `backend/routers/notifications.py` - 通知管理

### 前端文件
- `frontend/src/api/index.js` - API接口定义
- `frontend/src/views/Topics.vue` - 课题列表页（新建）
- `frontend/src/views/TopicDetail.vue` - 课题详情页（新建）
- `frontend/src/router/index.js` - 路由配置
- `frontend/src/layouts/MainLayout.vue` - 主布局

## 部署步骤

1. 停止后端服务
2. 更新后端代码
3. 如有必要，执行数据迁移脚本
4. 启动后端服务
5. 重新编译前端代码
6. 部署前端代码
7. 验证功能正常

## 回滚方案

如需回滚，执行以下步骤：
1. 恢复代码到修改前的版本
2. 如已执行数据迁移，需要反向迁移数据库
3. 重启服务

---
**修改完成时间**: 2026-01-26 17:57
**修改人**: AI Assistant
