<template>
  <div class="profile-container">
    <el-row :gutter="20">
      <!-- 左侧：个人信息 -->
      <el-col :span="16">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">个人信息</span>
              <el-button
                v-if="!isEditing"
                type="primary"
                :icon="Edit"
                @click="startEdit"
              >
                编辑
              </el-button>
              <div v-else>
                <el-button @click="cancelEdit">取消</el-button>
                <el-button
                  type="primary"
                  :icon="Check"
                  @click="saveProfile"
                  :loading="saving"
                >
                  保存
                </el-button>
              </div>
            </div>
          </template>

          <el-form
            :model="profileForm"
            label-width="100px"
            class="profile-form"
          >
            <el-form-item label="用户名">
              <el-input v-model="profileForm.username" disabled />
            </el-form-item>

            <el-form-item label="姓名">
              <el-input
                v-model="profileForm.full_name"
                :disabled="!isEditing"
                placeholder="请输入姓名"
              />
            </el-form-item>

            <el-form-item label="邮箱">
              <el-input
                v-model="profileForm.email"
                :disabled="!isEditing"
                placeholder="请输入邮箱"
              />
            </el-form-item>

            <el-form-item label="角色">
              <el-tag :type="getRoleType(profileForm.role)">
                {{ getRoleName(profileForm.role) }}
              </el-tag>
            </el-form-item>

            <el-form-item label="注册时间">
              <span class="info-text">{{
                formatDate(profileForm.created_at)
              }}</span>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 修改密码 -->
        <el-card class="box-card mt-20">
          <template #header>
            <div class="card-header">
              <span class="card-title">修改密码</span>
            </div>
          </template>

          <el-form
            :model="passwordForm"
            :rules="passwordRules"
            ref="passwordFormRef"
            label-width="100px"
            class="password-form"
          >
            <el-form-item label="旧密码" prop="old_password">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                placeholder="请输入旧密码"
                show-password
              />
            </el-form-item>

            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="请输入新密码"
                show-password
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirm_password">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="changePassword"
                :loading="changingPassword"
              >
                修改密码
              </el-button>
              <el-button @click="resetPasswordForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：统计数据 -->
      <el-col :span="8">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">我的统计</span>
            </div>
          </template>

          <div class="stats-container">
            <div class="stat-item">
              <div class="stat-icon project">
                <el-icon><Folder /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">创建的项目</div>
                <div class="stat-value">{{ stats.created_projects }}</div>
              </div>
            </div>

            <div class="stat-item">
              <div class="stat-icon project-participated">
                <el-icon><FolderOpened /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">参与的项目</div>
                <div class="stat-value">{{ stats.participated_projects }}</div>
              </div>
            </div>

            <div class="stat-item">
              <div class="stat-icon task">
                <el-icon><List /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">分配的任务</div>
                <div class="stat-value">{{ stats.assigned_tasks }}</div>
              </div>
            </div>

            <div class="stat-item">
              <div class="stat-icon task-completed">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">完成的任务</div>
                <div class="stat-value">{{ stats.completed_tasks }}</div>
              </div>
            </div>

            <div class="stat-item">
              <div class="stat-icon bug-created">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">创建的BUG</div>
                <div class="stat-value">{{ stats.created_bugs }}</div>
              </div>
            </div>

            <div class="stat-item">
              <div class="stat-icon bug-assigned">
                <el-icon><Tools /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">分配的BUG</div>
                <div class="stat-value">{{ stats.assigned_bugs }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage } from "element-plus";
import {
  Edit,
  Check,
  Folder,
  FolderOpened,
  List,
  CircleCheck,
  Warning,
  Tools,
} from "@element-plus/icons-vue";
import { userAPI, authAPI } from "@/api";
import { useUserStore } from "@/stores/user";
import dayjs from "dayjs";

const userStore = useUserStore();

const isEditing = ref(false);
const saving = ref(false);
const changingPassword = ref(false);

const profileForm = reactive({
  username: "",
  full_name: "",
  email: "",
  role: "",
  created_at: "",
});

const originalProfile = ref({});

const passwordForm = reactive({
  old_password: "",
  new_password: "",
  confirm_password: "",
});

const passwordFormRef = ref(null);

const stats = reactive({
  created_projects: 0,
  participated_projects: 0,
  assigned_tasks: 0,
  completed_tasks: 0,
  created_bugs: 0,
  assigned_bugs: 0,
});

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error("两次输入的密码不一致"));
  } else {
    callback();
  }
};

const passwordRules = {
  old_password: [{ required: true, message: "请输入旧密码", trigger: "blur" }],
  new_password: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    { min: 6, message: "密码长度至少6位", trigger: "blur" },
  ],
  confirm_password: [
    { required: true, message: "请再次输入新密码", trigger: "blur" },
    { validator: validateConfirmPassword, trigger: "blur" },
  ],
};

const getRoleName = (role) => {
  const roleMap = {
    admin: "管理员",
    project_manager: "项目经理",
    developer: "开发人员",
    tester: "测试人员",
    external_personnel: "外来人员",
  };
  return roleMap[role] || role;
};

const getRoleType = (role) => {
  const typeMap = {
    admin: "danger",
    project_manager: "warning",
    developer: "primary",
    tester: "success",
    external_personnel: "info",
  };
  return typeMap[role] || "info";
};

const formatDate = (date) => {
  return date ? dayjs(date).format("YYYY-MM-DD HH:mm:ss") : "-";
};

const loadProfile = async () => {
  try {
    // 如果 store 中已有用户信息，直接使用
    if (userStore.user) {
      Object.assign(profileForm, userStore.user);
      originalProfile.value = { ...userStore.user };
    } else {
      // 否则重新获取
      await userStore.getCurrentUser();
      if (userStore.user) {
        Object.assign(profileForm, userStore.user);
        originalProfile.value = { ...userStore.user };
      }
    }
  } catch (error) {
    console.error("加载用户信息失败:", error);
    ElMessage.error("加载用户信息失败");
  }
};

const loadStats = async () => {
  try {
    const data = await userAPI.getUserStats();
    Object.assign(stats, data);
  } catch (error) {
    console.error("加载统计数据失败:", error);
    ElMessage.error("加载统计数据失败");
  }
};

const startEdit = () => {
  isEditing.value = true;
};

const cancelEdit = () => {
  Object.assign(profileForm, originalProfile.value);
  isEditing.value = false;
};

const saveProfile = async () => {
  if (!userStore.user?.id) {
    ElMessage.error("用户信息不完整，请重新登录");
    return;
  }

  saving.value = true;
  try {
    await userAPI.updateUser(userStore.user.id, {
      full_name: profileForm.full_name,
      email: profileForm.email,
    });

    // 更新 store 中的用户信息
    await userStore.getCurrentUser();

    // 重新加载个人信息
    if (userStore.user) {
      Object.assign(profileForm, userStore.user);
      originalProfile.value = { ...userStore.user };
    }

    isEditing.value = false;
    ElMessage.success("个人信息更新成功");
  } catch (error) {
    console.error("更新用户信息失败:", error);
    ElMessage.error(error.response?.data?.detail || "更新失败");
  } finally {
    saving.value = false;
  }
};

const changePassword = async () => {
  if (!passwordFormRef.value) return;

  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return;

    changingPassword.value = true;
    try {
      await userAPI.changePassword({
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password,
      });

      ElMessage.success("密码修改成功，请重新登录");
      resetPasswordForm();

      // 延迟后退出登录
      setTimeout(() => {
        userStore.logout();
      }, 1500);
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || "密码修改失败");
    } finally {
      changingPassword.value = false;
    }
  });
};

const resetPasswordForm = () => {
  passwordForm.old_password = "";
  passwordForm.new_password = "";
  passwordForm.confirm_password = "";
  passwordFormRef.value?.clearValidate();
};

onMounted(() => {
  loadProfile();
  loadStats();
});
</script>

<style scoped>
.profile-container {
  padding: 20px;
}

.box-card {
  border-radius: 8px;
}

.mt-20 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

.profile-form,
.password-form {
  padding: 20px 0;
}

.info-text {
  color: #606266;
}

.stats-container {
  padding: 10px 0;
}

.stat-item {
  display: flex;
  align-items: center;
  padding: 15px;
  margin-bottom: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s;
}

.stat-item:hover {
  background: #ecf5ff;
  transform: translateX(5px);
}

.stat-item:last-child {
  margin-bottom: 0;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-right: 15px;
}

.stat-icon.project {
  background: #e6f7ff;
  color: #1890ff;
}

.stat-icon.project-participated {
  background: #f0f9ff;
  color: #0ea5e9;
}

.stat-icon.task {
  background: #fff7e6;
  color: #fa8c16;
}

.stat-icon.task-completed {
  background: #f6ffed;
  color: #52c41a;
}

.stat-icon.bug-created {
  background: #fff1f0;
  color: #ff4d4f;
}

.stat-icon.bug-assigned {
  background: #f9f0ff;
  color: #722ed1;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}
</style>

