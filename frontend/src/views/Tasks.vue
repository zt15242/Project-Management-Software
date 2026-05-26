<template>
  <div class="tasks">
    <div class="page-header">
      <h1>任务管理</h1>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog"
        >创建任务</el-button
      >
    </div>

    <el-card>
      <div class="filter-bar">
        <el-select
          v-model="filters.project_id"
          placeholder="选择项目"
          clearable
          @change="fetchTasks"
          style="width: 200px"
        >
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>
        <el-select
          v-model="filters.status"
          placeholder="任务状态"
          clearable
          @change="fetchTasks"
          style="width: 150px"
        >
          <el-option label="待办" value="todo" />
          <el-option label="进行中" value="in_progress" />
          <el-option label="已完成" value="completed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
        <el-select
          v-model="filters.assigned_to"
          placeholder="负责人"
          clearable
          @change="fetchTasks"
          style="width: 150px"
        >
          <el-option
            v-for="user in users"
            :key="user.id"
            :label="user.full_name"
            :value="user.id"
          />
        </el-select>
      </div>

      <el-table
        :data="tasks"
        stripe
        border
        style="width: 100%; margin-top: 20px"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
      >
        <el-table-column
          prop="title"
          label="任务标题"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column label="项目" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            {{ getProjectName(row.project_id) }}
          </template>
        </el-table-column>
        <el-table-column label="负责人" width="100" align="center">
          <template #default="{ row }">
            <span v-if="getUserName(row.assigned_to)">{{
              getUserName(row.assigned_to)
            }}</span>
            <span v-else style="color: #909399">未分配</span>
          </template>
        </el-table-column>
        <el-table-column label="协助人" width="140" align="center">
          <template #default="{ row }">
            <span v-if="row.collaborators && row.collaborators.length > 0">
              <el-tag
                v-for="id in row.collaborators.slice(0, 2)"
                :key="id"
                size="small"
                style="margin-right: 4px"
              >
                {{ getUserName(id) }}
              </el-tag>
              <el-tag
                v-if="row.collaborators.length > 2"
                size="small"
                type="info"
              >
                +{{ row.collaborators.length - 2 }}
              </el-tag>
            </span>
            <span v-else style="color: #909399">-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="优先级" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">
              {{ getPriorityLabel(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="截止日期" width="110" align="center">
          <template #default="{ row }">
            <span v-if="row.due_date">{{ formatDate(row.due_date) }}</span>
            <span v-else style="color: #909399">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" :icon="Edit" @click="handleEdit(row)"
              >编辑</el-button
            >
            <el-button
              link
              type="danger"
              :icon="Delete"
              @click="handleDelete(row)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑任务对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form
        :model="taskForm"
        :rules="rules"
        ref="formRef"
        label-width="100px"
      >
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="taskForm.title" />
        </el-form-item>
        <el-form-item label="任务描述" prop="description">
          <el-input v-model="taskForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="所属项目" prop="project_id">
          <el-select
            v-model="taskForm.project_id"
            placeholder="选择项目"
            style="width: 100%"
            :disabled="isEdit"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-select
            v-model="taskForm.assigned_to"
            placeholder="选择负责人"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="`${user.full_name} (${user.username})`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="协助人">
          <el-select
            v-model="taskForm.collaborators"
            placeholder="选择协助人（可多选）"
            multiple
            clearable
            style="width: 100%"
            collapse-tags
            collapse-tags-tooltip
          >
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="`${user.full_name} (${user.username})`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-radio-group v-model="taskForm.priority">
            <el-radio label="low">低</el-radio>
            <el-radio label="medium">中</el-radio>
            <el-radio label="high">高</el-radio>
            <el-radio label="urgent">紧急</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="状态" v-if="isEdit">
          <el-radio-group v-model="taskForm.status">
            <el-radio label="todo">待办</el-radio>
            <el-radio label="in_progress">进行中</el-radio>
            <el-radio label="completed">已完成</el-radio>
            <el-radio label="cancelled">已取消</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="预估工时">
          <el-input-number
            v-model="taskForm.estimated_hours"
            :min="0"
            :step="0.5"
          />
          <span style="margin-left: 10px">小时</span>
        </el-form-item>
        <el-form-item label="实际工时" v-if="isEdit">
          <el-input-number
            v-model="taskForm.actual_hours"
            :min="0"
            :step="0.5"
          />
          <span style="margin-left: 10px">小时</span>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="taskForm.due_date"
            type="datetime"
            placeholder="选择日期时间"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting"
          >确定</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from "vue";
import { taskAPI, projectAPI, userAPI } from "@/api";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Edit, Delete } from "@element-plus/icons-vue";
import dayjs from "dayjs";

const tasks = ref([]);
const projects = ref([]);
const users = ref([]);
const dialogVisible = ref(false);
const formRef = ref();
const submitting = ref(false);
const isEdit = ref(false);
const currentTask = ref(null);

const filters = reactive({
  project_id: "",
  status: "",
  assigned_to: "",
});

const taskForm = reactive({
  title: "",
  description: "",
  project_id: "",
  assigned_to: "",
  collaborators: [],
  priority: "medium",
  status: "todo",
  estimated_hours: 0,
  actual_hours: 0,
  due_date: null,
});

const rules = {
  title: [{ required: true, message: "请输入任务标题", trigger: "blur" }],
  project_id: [{ required: true, message: "请选择项目", trigger: "change" }],
  priority: [{ required: true, message: "请选择优先级", trigger: "change" }],
};

const dialogTitle = computed(() => (isEdit.value ? "编辑任务" : "创建任务"));

const fetchTasks = async () => {
  try {
    const params = {};
    if (filters.project_id) params.project_id = filters.project_id;
    if (filters.status) params.status = filters.status;
    if (filters.assigned_to) params.assigned_to = filters.assigned_to;
    tasks.value = await taskAPI.getTasks(params);
  } catch (error) {
    ElMessage.error("获取任务列表失败");
  }
};

const fetchProjects = async () => {
  try {
    const data = await projectAPI.getProjects({ limit: 100 });
    projects.value = data.items || [];
  } catch (error) {
    ElMessage.error("获取项目列表失败");
  }
};

const fetchUsers = async () => {
  try {
    users.value = await userAPI.getUsers();
  } catch (error) {
    ElMessage.error("获取用户列表失败");
  }
};

const showCreateDialog = () => {
  isEdit.value = false;
  Object.assign(taskForm, {
    title: "",
    description: "",
    project_id: filters.project_id || "",
    assigned_to: "",
    collaborators: [],
    priority: "medium",
    status: "todo",
    estimated_hours: 0,
    actual_hours: 0,
    due_date: null,
  });
  dialogVisible.value = true;
};

const handleEdit = (task) => {
  isEdit.value = true;
  currentTask.value = task;
  Object.assign(taskForm, {
    title: task.title,
    description: task.description,
    project_id: task.project_id,
    assigned_to: task.assigned_to,
    collaborators: task.collaborators || [],
    priority: task.priority,
    status: task.status,
    estimated_hours: task.estimated_hours,
    actual_hours: task.actual_hours,
    due_date: task.due_date ? new Date(task.due_date) : null,
  });
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  const valid = await formRef.value.validate();
  if (!valid) return;

  submitting.value = true;
  try {
    if (isEdit.value) {
      await taskAPI.updateTask(currentTask.value.id, taskForm);
      ElMessage.success("任务更新成功");
    } else {
      await taskAPI.createTask(taskForm);
      ElMessage.success("任务创建成功");
    }
    dialogVisible.value = false;
    fetchTasks();
  } catch (error) {
    ElMessage.error("操作失败");
  } finally {
    submitting.value = false;
  }
};

const handleDelete = async (task) => {
  try {
    await ElMessageBox.confirm("确定要删除这个任务吗？", "提示", {
      type: "warning",
    });
    await taskAPI.deleteTask(task.id);
    ElMessage.success("删除成功");
    fetchTasks();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
};

const getProjectName = (projectId) => {
  const project = projects.value.find((p) => p.id === projectId);
  return project ? project.name : "未知项目";
};

const getUserName = (userId) => {
  if (!userId) return null;
  const user = users.value.find((u) => u.id === userId);
  return user ? user.full_name : "未知用户";
};

const getStatusType = (status) => {
  const types = {
    todo: "info",
    in_progress: "warning",
    completed: "success",
    cancelled: "danger",
  };
  return types[status] || "info";
};

const getStatusLabel = (status) => {
  const labels = {
    todo: "待办",
    in_progress: "进行中",
    completed: "已完成",
    cancelled: "已取消",
  };
  return labels[status] || status;
};

const getPriorityType = (priority) => {
  const types = {
    low: "info",
    medium: "",
    high: "warning",
    urgent: "danger",
  };
  return types[priority] || "";
};

const getPriorityLabel = (priority) => {
  const labels = {
    low: "低",
    medium: "中",
    high: "高",
    urgent: "紧急",
  };
  return labels[priority] || priority;
};

const formatDate = (date) => {
  return dayjs(date).format("YYYY-MM-DD");
};

onMounted(() => {
  fetchTasks();
  fetchProjects();
  fetchUsers();
});
</script>

<style scoped>
.tasks {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filter-bar {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

:deep(.el-card__body) {
  padding: 20px;
}

.el-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
</style>

