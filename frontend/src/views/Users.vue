<template>
  <div class="users">
    <div class="page-header">
      <h1>用户管理</h1>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog"
        >创建用户</el-button
      >
    </div>

    <el-card class="table-card">
      <el-table
        :data="users"
        stripe
        border
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
      >
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="full_name" label="姓名" width="120" />
        <el-table-column
          prop="email"
          label="邮箱"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column label="角色" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)" size="small">
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? "激活" : "未激活" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170" align="center">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" align="center">
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

    <!-- 创建/编辑用户对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form
        :model="userForm"
        :rules="rules"
        ref="formRef"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="userForm.username"
            :disabled="isEdit"
            placeholder="请输入用户名"
          />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="userForm.full_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input
            v-model="userForm.password"
            type="password"
            placeholder="请输入密码（至少6位）"
          />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select
            v-model="userForm.role"
            placeholder="选择角色"
            style="width: 100%"
          >
            <el-option label="管理员" value="admin" />
            <el-option label="项目经理" value="project_manager" />
            <el-option label="开发人员" value="developer" />
            <el-option label="测试人员" value="tester" />
            <el-option label="外来人员" value="external_personnel" />
          </el-select>
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
import { userAPI, authAPI } from "@/api";
import { ElMessage, ElMessageBox } from "element-plus";
import { Edit, Delete, Plus } from "@element-plus/icons-vue";
import dayjs from "dayjs";

const users = ref([]);
const dialogVisible = ref(false);
const formRef = ref();
const submitting = ref(false);
const currentUser = ref(null);
const isEdit = ref(false);

const userForm = reactive({
  username: "",
  full_name: "",
  email: "",
  password: "",
  role: "",
});

const dialogTitle = computed(() => (isEdit.value ? "编辑用户" : "创建用户"));

const rules = computed(() => {
  const baseRules = {
    username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
    full_name: [{ required: true, message: "请输入姓名", trigger: "blur" }],
    email: [
      { required: true, message: "请输入邮箱", trigger: "blur" },
      { type: "email", message: "请输入有效的邮箱地址", trigger: "blur" },
    ],
    role: [{ required: true, message: "请选择角色", trigger: "change" }],
  };

  if (!isEdit.value) {
    baseRules.password = [
      { required: true, message: "请输入密码", trigger: "blur" },
      { min: 6, message: "密码长度至少6位", trigger: "blur" },
    ];
  }

  return baseRules;
});

const fetchUsers = async () => {
  try {
    users.value = await userAPI.getUsers();
  } catch (error) {
    ElMessage.error("获取用户列表失败");
  }
};

const showCreateDialog = () => {
  isEdit.value = false;
  currentUser.value = null;
  Object.assign(userForm, {
    username: "",
    full_name: "",
    email: "",
    password: "",
    role: "developer",
  });
  dialogVisible.value = true;
};

const handleEdit = (user) => {
  isEdit.value = true;
  currentUser.value = user;
  Object.assign(userForm, {
    username: user.username,
    full_name: user.full_name,
    email: user.email,
    password: "",
    role: user.role,
  });
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  const valid = await formRef.value.validate();
  if (!valid) return;

  submitting.value = true;
  try {
    if (isEdit.value) {
      // 编辑用户
      const updateData = {
        full_name: userForm.full_name,
        email: userForm.email,
        role: userForm.role,
      };
      await userAPI.updateUser(currentUser.value.id, updateData);
      ElMessage.success("用户更新成功");
    } else {
      // 创建用户
      await authAPI.register({
        username: userForm.username,
        full_name: userForm.full_name,
        email: userForm.email,
        password: userForm.password,
        role: userForm.role,
      });
      ElMessage.success("用户创建成功");
    }
    dialogVisible.value = false;
    fetchUsers();
  } catch (error) {
    ElMessage.error(isEdit.value ? "更新失败" : "创建失败");
  } finally {
    submitting.value = false;
  }
};

const handleDelete = async (user) => {
  try {
    await ElMessageBox.confirm("确定要删除这个用户吗？", "提示", {
      type: "warning",
    });
    await userAPI.deleteUser(user.id);
    ElMessage.success("删除成功");
    fetchUsers();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
};

const getRoleType = (role) => {
  const types = {
    admin: "danger",
    project_manager: "warning",
    developer: "success",
    tester: "info",
    external_personnel: "",
  };
  return types[role] || "";
};

const getRoleLabel = (role) => {
  const labels = {
    admin: "管理员",
    project_manager: "项目经理",
    developer: "开发人员",
    tester: "测试人员",
    external_personnel: "外来人员",
  };
  return labels[role] || role;
};

const formatDateTime = (date) => {
  return dayjs(date).format("YYYY-MM-DD HH:mm:ss");
};

onMounted(() => {
  fetchUsers();
});
</script>

<style scoped>
.users {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.table-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.table-card :deep(.el-table) {
  font-size: 14px;
}

.table-card :deep(.el-table td),
.table-card :deep(.el-table th) {
  padding: 12px 0;
}
</style>
