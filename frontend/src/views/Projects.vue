<template>
  <div class="projects">
    <div class="page-header">
      <div class="header-left">
        <h1>项目管理</h1>
        <el-input
          v-model="searchQuery"
          placeholder="搜索项目名称或内容..."
          :prefix-icon="Search"
          clearable
          class="search-input"
          @input="handleSearch"
        />
      </div>
      <el-button
        v-if="canCreateProject"
        type="primary"
        :icon="Plus"
        @click="showCreateDialog"
      >
        创建项目
      </el-button>
    </div>

    <!-- 权限提示 -->
    <el-alert
      v-if="!isAdmin && userRole !== 'project_manager'"
      type="info"
      :closable="false"
      style="margin-bottom: 20px"
    >
      <template #title>
        <span
          >您当前只能查看自己参与的项目。如需查看更多，请联系系统管理员。</span
        >
      </template>
    </el-alert>

    <div v-loading="loading">
      <el-row :gutter="20" v-if="projects.length > 0">
        <el-col :span="8" v-for="project in projects" :key="project.id">
          <el-card class="project-card" @click="goToProjectDetail(project.id)">
            <template #header>
              <div class="card-header">
                <span class="project-name">{{ project.name }}</span>
                <el-tag :type="project.is_active ? 'success' : 'info'">
                  {{ project.is_active ? "进行中" : "已结束" }}
                </el-tag>
              </div>
            </template>
            <div class="project-content">
              <p class="project-desc">
                {{ project.description || "暂无描述" }}
              </p>
              <div class="project-info">
                <div class="info-item">
                  <el-icon><User /></el-icon>
                  <span>{{ project.team_members.length }} 人</span>
                </div>
                <div class="info-item">
                  <el-icon><Calendar /></el-icon>
                  <span>{{ formatDate(project.created_at) }}</span>
                </div>
              </div>
            </div>
            <template #footer>
              <div class="card-footer">
                <el-button
                  v-if="canEditProject(project)"
                  text
                  :icon="Edit"
                  @click.stop="handleEdit(project)"
                >
                  编辑
                </el-button>
                <el-button
                  v-if="canEditProject(project)"
                  text
                  :icon="UserFilled"
                  @click.stop="handleManageMembers(project)"
                >
                  成员
                </el-button>
              </div>
            </template>
          </el-card>
        </el-col>
      </el-row>

      <el-empty v-else description="暂无项目数据" />

      <!-- 分页 -->
      <div class="pagination-container" v-if="total > 0">
        <el-pagination
          :current-page="currentPage"
          @update:current-page="(val) => (currentPage = val)"
          :page-size="pageSize"
          @update:page-size="(val) => (pageSize = val)"
          :page-sizes="[12, 24, 48, 96]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 创建/编辑项目对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form
        :model="projectForm"
        :rules="rules"
        ref="formRef"
        label-width="100px"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="projectForm.name" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="projectForm.description"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="项目经理">
          <el-select
            v-model="projectForm.project_manager_id"
            placeholder="选择项目经理（可选）"
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
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="projectForm.start_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="projectForm.end_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="状态" v-if="isEdit">
          <el-switch
            v-model="projectForm.is_active"
            active-text="进行中"
            inactive-text="已结束"
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

    <!-- 管理成员对话框 -->
    <el-dialog v-model="memberDialogVisible" title="管理项目成员" width="600px">
      <!-- ... same as before ... -->
      <div class="member-management">
        <div class="add-member">
          <el-select
            v-model="selectedUserId"
            placeholder="选择成员"
            style="width: 300px"
          >
            <el-option
              v-for="user in availableUsers"
              :key="user.id"
              :label="`${user.full_name} (${user.username})`"
              :value="user.id"
            />
          </el-select>
          <el-button
            type="primary"
            @click="handleAddMember"
            :disabled="!selectedUserId"
            >添加</el-button
          >
        </div>
        <el-divider />
        <div class="member-list">
          <div
            v-for="memberId in currentProject?.team_members"
            :key="memberId"
            class="member-item"
          >
            <div class="member-info">
              <el-avatar :size="32" :icon="UserFilled" />
              <span>{{ getUserName(memberId) }}</span>
              <el-tag
                v-if="memberId === currentProject?.owner_id"
                type="warning"
                size="small"
                >所有者</el-tag
              >
              <el-tag
                v-if="memberId === currentProject?.project_manager_id"
                type="primary"
                size="small"
                >项目经理</el-tag
              >
            </div>
            <el-button
              v-if="
                memberId !== currentProject?.owner_id &&
                memberId !== currentProject?.project_manager_id
              "
              type="danger"
              text
              :icon="Delete"
              @click="handleRemoveMember(memberId)"
            >
              移除
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from "vue";
import { useRouter } from "vue-router";
import { projectAPI, userAPI } from "@/api";
import { ElMessage } from "element-plus";
import {
  Plus,
  Edit,
  User,
  UserFilled,
  Calendar,
  Delete,
  Search,
} from "@element-plus/icons-vue";
import { useUserStore } from "@/stores/user";
import dayjs from "dayjs";

const router = useRouter();
const userStore = useUserStore();
const projects = ref([]);
const users = ref([]);
const dialogVisible = ref(false);
const memberDialogVisible = ref(false);
const formRef = ref();
const submitting = ref(false);
const loading = ref(false);
const isEdit = ref(false);
const currentProject = ref(null);
const selectedUserId = ref("");

// 搜索和分页
const searchQuery = ref("");
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(12);

// 当前用户信息
const currentUserId = computed(() => userStore.userId);
const isAdmin = computed(() => userStore.isAdmin);
const userRole = computed(() => userStore.role);

// 判断是否可以创建项目：管理员或项目经理
const canCreateProject = computed(() => {
  return isAdmin.value || userRole.value === "project_manager";
});

// 判断是否可以编辑项目：管理员、项目所有者或项目经理
const canEditProject = (project) => {
  if (isAdmin.value) return true;
  if (project.owner_id === currentUserId.value) return true;
  if (project.project_manager_id === currentUserId.value) return true;
  return false;
};

const projectForm = reactive({
  name: "",
  description: "",
  project_manager_id: null,
  start_date: null,
  end_date: null,
  is_active: true,
});

const rules = {
  name: [{ required: true, message: "请输入项目名称", trigger: "blur" }],
};

const dialogTitle = computed(() => (isEdit.value ? "编辑项目" : "创建项目"));

const availableUsers = computed(() => {
  if (!currentProject.value) return users.value;
  return users.value.filter(
    (u) => !currentProject.value.team_members.includes(u.id)
  );
});

const fetchProjects = async () => {
  loading.value = true;
  try {
    const params = {
      search: searchQuery.value || undefined,
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    };
    const res = await projectAPI.getProjects(params);
    projects.value = res.items;
    total.value = res.total;
  } catch (error) {
    ElMessage.error("获取项目列表失败");
  } finally {
    loading.value = false;
  }
};

const fetchUsers = async () => {
  try {
    users.value = await userAPI.getUsers();
  } catch (error) {
    ElMessage.error("获取用户列表失败");
  }
};

// 自定义 debounce 函数
const debounce = (fn, delay) => {
  let timer = null;
  return function (...args) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fn.apply(this, args);
    }, delay);
  };
};

const handleSearch = debounce(() => {
  currentPage.value = 1;
  fetchProjects();
}, 300);

const handlePageChange = (page) => {
  currentPage.value = page;
  fetchProjects();
};

const handleSizeChange = (size) => {
  pageSize.value = size;
  currentPage.value = 1;
  fetchProjects();
};

const showCreateDialog = () => {
  isEdit.value = false;
  Object.assign(projectForm, {
    name: "",
    description: "",
    project_manager_id: null,
    start_date: null,
    end_date: null,
    is_active: true,
  });
  dialogVisible.value = true;
};

const handleEdit = (project) => {
  isEdit.value = true;
  currentProject.value = project;
  Object.assign(projectForm, {
    name: project.name,
    description: project.description,
    project_manager_id: project.project_manager_id,
    start_date: project.start_date ? new Date(project.start_date) : null,
    end_date: project.end_date ? new Date(project.end_date) : null,
    is_active: project.is_active,
  });
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  const valid = await formRef.value.validate();
  if (!valid) return;

  submitting.value = true;
  try {
    if (isEdit.value) {
      await projectAPI.updateProject(currentProject.value.id, projectForm);
      ElMessage.success("项目更新成功");
    } else {
      await projectAPI.createProject(projectForm);
      ElMessage.success("项目创建成功");
    }
    dialogVisible.value = false;
    fetchProjects();
  } catch (error) {
    if (error.response?.status === 403) {
      ElMessage.error(error.response?.data?.detail || "没有权限执行此操作");
    } else {
      ElMessage.error("操作失败");
    }
  } finally {
    submitting.value = false;
  }
};

const handleManageMembers = (project) => {
  currentProject.value = project;
  selectedUserId.value = "";
  memberDialogVisible.value = true;
};

const handleAddMember = async () => {
  try {
    await projectAPI.addMember(currentProject.value.id, selectedUserId.value);
    ElMessage.success("添加成员成功");
    await fetchProjects();
    const updatedProject = projects.value.find(
      (p) => p.id === currentProject.value.id
    );
    if (updatedProject) {
      currentProject.value = updatedProject;
    }
    selectedUserId.value = "";
  } catch (error) {
    if (error.response?.status === 403) {
      ElMessage.error(error.response?.data?.detail || "没有权限执行此操作");
    } else {
      ElMessage.error("添加成员失败");
    }
  }
};

const handleRemoveMember = async (userId) => {
  try {
    await projectAPI.removeMember(currentProject.value.id, userId);
    ElMessage.success("移除成员成功");
    await fetchProjects();
    const updatedProject = projects.value.find(
      (p) => p.id === currentProject.value.id
    );
    if (updatedProject) {
      currentProject.value = updatedProject;
    }
  } catch (error) {
    ElMessage.error("移除成员失败");
  }
};

const getUserName = (userId) => {
  const user = users.value.find((u) => u.id === userId);
  return user ? `${user.full_name} (${user.username})` : "未知用户";
};

const goToProjectDetail = (projectId) => {
  router.push(`/projects/${projectId}`);
};

const formatDate = (date) => {
  return dayjs(date).format("YYYY-MM-DD");
};

onMounted(() => {
  fetchProjects();
  fetchUsers();
});
</script>

<style scoped>
.projects {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.search-input {
  width: 300px;
}

.project-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.project-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-name {
  font-weight: bold;
  font-size: 16px;
}

.project-content {
  min-height: 100px;
}

.project-desc {
  color: #666;
  margin-bottom: 15px;
  min-height: 40px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.5;
}

.project-info {
  display: flex;
  gap: 20px;
  color: #999;
  font-size: 14px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.pagination-container {
  margin-top: 30px;
  display: flex;
  justify-content: center;
}

.member-management {
  padding: 10px 0;
}

.add-member {
  display: flex;
  gap: 10px;
}

.member-list {
  max-height: 400px;
  overflow-y: auto;
}

.member-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.member-info {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
