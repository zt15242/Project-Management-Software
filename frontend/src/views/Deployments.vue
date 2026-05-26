<template>
  <div class="deployments-page">
    <div class="page-header">
      <h1>代码发布管理</h1>
      <div class="header-actions">
        <el-button
          type="primary"
          @click="showCreateDialog = true"
          v-if="canCreateDeployment"
        >
          <el-icon><Plus /></el-icon>
          新建发布包
        </el-button>
      </div>
    </div>

    <!-- 筛选器 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" label-width="90px">
        <el-form-item label="项目">
          <el-select
            v-model="filters.project_id"
            placeholder="选择项目"
            clearable
            @change="loadDeployments"
            style="width: 200px"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="发布类型">
          <el-select
            v-model="filters.deployment_type"
            placeholder="选择类型"
            clearable
            @change="loadDeployments"
            style="width: 200px"
          >
            <el-option label="逻辑代码包" value="logic_code" />
            <el-option label="页面代码" value="page_code" />
          </el-select>
        </el-form-item>
        <el-form-item label-width="0">
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 发布包列表 -->
    <el-card class="deployments-list">
      <el-table
        :data="deployments"
        v-loading="loading"
        stripe
        @row-click="viewDetail"
      >
        <el-table-column prop="title" label="包名称" min-width="200" />
        <el-table-column prop="deployment_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag
              :type="
                row.deployment_type === 'logic_code' ? 'primary' : 'success'
              "
            >
              {{
                row.deployment_type === "logic_code" ? "逻辑代码" : "页面代码"
              }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_version" label="当前版本" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.current_version > 0" type="info"
              >v{{ row.current_version }}</el-tag
            >
            <span v-else class="text-muted">无版本</span>
          </template>
        </el-table-column>
        <el-table-column label="版本数量" width="100">
          <template #default="{ row }">
            {{ row.versions.length }}
          </template>
        </el-table-column>
        <el-table-column label="最新状态" width="120">
          <template #default="{ row }">
            <el-tag
              v-if="row.versions.length > 0"
              :type="
                getStatusType(row.versions[row.versions.length - 1].status)
              "
            >
              {{ getStatusText(row.versions[row.versions.length - 1].status) }}
            </el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="viewDetail(row)"
              >详情</el-button
            >
            <el-button link type="success" @click.stop="showUploadDialog(row)"
              >上传版本</el-button
            >
            <el-button
              link
              type="danger"
              @click.stop="handleDelete(row)"
              v-if="canDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建发布包对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建发布包" width="600px">
      <el-form
        :model="createForm"
        :rules="createRules"
        ref="createFormRef"
        label-width="100px"
      >
        <el-form-item label="标题" prop="title">
          <el-input
            v-model="createForm.title"
            placeholder="请输入包名称（用作标题）"
          />
          <div class="form-tip">包名称将在后续版本中继续使用</div>
        </el-form-item>

        <el-form-item label="项目" prop="project_id">
          <el-select
            v-model="createForm.project_id"
            placeholder="选择项目"
            style="width: 100%"
            @change="handleProjectChange"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item
          label="环境配置"
          v-if="createForm.deployment_type === 'logic_code'"
        >
          <el-select
            v-model="createForm.environment_id"
            placeholder="选择环境配置（可选）"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="env in projectEnvironments"
              :key="env.id"
              :label="env.name"
              :value="env.id"
            />
          </el-select>
          <div class="form-tip">选择环境后可自动匹配远程包</div>
        </el-form-item>

        <el-form-item
          label="包路径"
          v-if="
            createForm.deployment_type === 'logic_code' &&
            createForm.environment_id
          "
        >
          <el-input
            v-model="createForm.package_path"
            placeholder="如：other.oa.message"
          />
          <div class="form-tip">保存时将自动匹配或创建远程包</div>
        </el-form-item>

        <el-form-item label="发布类型" prop="deployment_type">
          <el-radio-group v-model="createForm.deployment_type">
            <el-radio label="logic_code">逻辑代码包</el-radio>
            <el-radio label="page_code">页面代码</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入发布说明"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="submitting"
          >提交</el-button
        >
      </template>
    </el-dialog>

    <!-- 上传版本对话框 -->
    <el-dialog
      v-model="showUploadVersionDialog"
      title="上传新版本"
      width="600px"
    >
      <div class="upload-info">
        <p><strong>包名称：</strong>{{ selectedDeployment?.title }}</p>
        <p>
          <strong>当前版本：</strong>v{{
            selectedDeployment?.current_version || 0
          }}
        </p>
        <p>
          <strong>新版本号：</strong>v{{
            (selectedDeployment?.current_version || 0) + 1
          }}
        </p>
      </div>

      <el-form :model="uploadForm" ref="uploadFormRef" label-width="100px">
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入本次版本的更新说明"
          />
        </el-form-item>

        <el-form-item label="代码包" prop="file" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".zip"
            :on-change="handleFileChange"
            :file-list="fileList"
          >
            <el-button type="primary">选择ZIP文件</el-button>
            <template #tip>
              <div class="el-upload__tip">只能上传.zip文件</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showUploadVersionDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleUploadVersion"
          :loading="submitting"
          >提交</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus } from "@element-plus/icons-vue";
import { deploymentAPI, projectAPI, environmentAPI } from "@/api";
import { useUserStore } from "@/stores/user";

const router = useRouter();
const userStore = useUserStore();

// 状态
const loading = ref(false);
const submitting = ref(false);
const deployments = ref([]);
const projects = ref([]);
const projectEnvironments = ref([]);

// 筛选器
const filters = ref({
  project_id: "",
  deployment_type: "",
});

// 对话框
const showCreateDialog = ref(false);
const showUploadVersionDialog = ref(false);
const selectedDeployment = ref(null);

// 表单
const createFormRef = ref();
const uploadFormRef = ref();
const uploadRef = ref();
const fileList = ref([]);

const createForm = ref({
  title: "",
  project_id: "",
  deployment_type: "logic_code",
  description: "",
  environment_id: "",
  package_path: "",
  remote_package_id: "",
});

const uploadForm = ref({
  description: "",
  file: null,
});

const createRules = {
  title: [{ required: true, message: "请输入包名称", trigger: "blur" }],
  project_id: [{ required: true, message: "请选择项目", trigger: "change" }],
  deployment_type: [
    { required: true, message: "请选择发布类型", trigger: "change" },
  ],
};

// 权限判断
const canCreateDeployment = computed(() => {
  return ["admin", "project_manager", "developer"].includes(
    userStore.user?.role
  );
});

const canDelete = (deployment) => {
  return (
    userStore.user?.role === "admin" ||
    userStore.user?.role === "project_manager" ||
    deployment.created_by === userStore.user?.id
  );
};

// 加载数据
const loadDeployments = async () => {
  loading.value = true;
  try {
    const params = {};
    if (filters.value.project_id) params.project_id = filters.value.project_id;
    if (filters.value.deployment_type)
      params.deployment_type = filters.value.deployment_type;

    const response = await deploymentAPI.getDeployments(params);
    // 响应拦截器已经返回了 response.data，所以这里直接使用 response
    deployments.value = response;
  } catch (error) {
    ElMessage.error("加载发布列表失败");
  } finally {
    loading.value = false;
  }
};

const loadProjects = async () => {
  try {
    const response = await projectAPI.getProjects({ limit: 100 });
    // 分页接口返回 { items, total }
    projects.value = response.items || [];
    console.log("加载到的项目列表:", projects.value);
  } catch (error) {
    console.error("加载项目列表失败", error);
    ElMessage.error(
      "加载项目列表失败: " + (error.response?.data?.detail || error.message)
    );
  }
};

// 项目变更时加载环境配置
const handleProjectChange = async (projectId) => {
  projectEnvironments.value = [];
  createForm.value.environment_id = "";
  createForm.value.package_path = "";
  createForm.value.remote_package_id = "";

  if (!projectId) return;

  try {
    const response = await environmentAPI.getProjectEnvironments(projectId);
    projectEnvironments.value = response;
  } catch (error) {
    ElMessage.error("加载环境配置失败");
  }
};

// 包路径失焦时匹配或创建远程包
const handlePackagePathBlur = async () => {
  const { environment_id, package_path, title } = createForm.value;

  if (!environment_id || !package_path) {
    return;
  }

  if (!title) {
    ElMessage.warning("请先输入包名称");
    return;
  }

  try {
    const response = await deploymentAPI.matchOrCreatePackage(environment_id, {
      package_path,
      package_name: title,
    });

    createForm.value.remote_package_id = response.package_id;

    if (response.matched) {
      ElMessage.success(`已匹配到现有包：${response.package_title}`);
    } else if (response.created) {
      ElMessage.success(`已创建新包：${response.package_title}`);
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "匹配或创建包失败");
  }
};

// 重置筛选器
const resetFilters = () => {
  filters.value = {
    project_id: "",
    deployment_type: "",
  };
  loadDeployments();
};

// 创建发布包
const handleCreate = async () => {
  if (!createFormRef.value) return;

  await createFormRef.value.validate(async (valid) => {
    if (!valid) return;

    submitting.value = true;
    try {
      await deploymentAPI.createDeployment(createForm.value);
      ElMessage.success("发布包创建成功");
      showCreateDialog.value = false;
      resetCreateForm();
      loadDeployments();
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || "创建失败");
    } finally {
      submitting.value = false;
    }
  });
};

const resetCreateForm = () => {
  createForm.value = {
    title: "",
    project_id: "",
    deployment_type: "logic_code",
    description: "",
    environment_id: "",
    package_path: "",
    remote_package_id: "",
  };
  projectEnvironments.value = [];
  createFormRef.value?.resetFields();
};

// 上传版本
const showUploadDialog = (deployment) => {
  selectedDeployment.value = deployment;
  uploadForm.value = {
    description: "",
    file: null,
  };
  fileList.value = [];
  showUploadVersionDialog.value = true;
};

const handleFileChange = (file) => {
  uploadForm.value.file = file.raw;
  fileList.value = [file];
};

const handleUploadVersion = async () => {
  if (!uploadForm.value.file) {
    ElMessage.warning("请选择要上传的文件");
    return;
  }

  submitting.value = true;
  try {
    await deploymentAPI.uploadVersion(
      selectedDeployment.value.id,
      uploadForm.value
    );
    ElMessage.success("版本上传成功，AI分析中...");
    showUploadVersionDialog.value = false;
    loadDeployments();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "上传失败");
  } finally {
    submitting.value = false;
  }
};

// 查看详情
const viewDetail = (row) => {
  router.push(`/deployments/${row.id}`);
};

// 删除
const handleDelete = async (deployment) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除发布包"${deployment.title}"吗？这将删除所有版本！`,
      "确认删除",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }
    );

    await deploymentAPI.deleteDeployment(deployment.id);
    ElMessage.success("删除成功");
    loadDeployments();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
};

// 工具函数
const getStatusType = (status) => {
  const statusMap = {
    pending: "warning",
    analyzing: "info",
    analysis_completed: "primary",
    approved: "success",
    rejected: "danger",
    deploying: "info",
    deployed: "success",
    failed: "danger",
  };
  return statusMap[status] || "info";
};

const getStatusText = (status) => {
  const statusMap = {
    pending: "待审核",
    analyzing: "分析中",
    analysis_completed: "分析完成",
    approved: "审核通过",
    rejected: "审核拒绝",
    deploying: "部署中",
    deployed: "已部署",
    failed: "部署失败",
  };
  return statusMap[status] || status;
};

const formatDate = (dateString) => {
  if (!dateString) return "-";
  const date = new Date(dateString);
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// 初始化
onMounted(() => {
  console.log("Deployments 组件已挂载，开始加载数据...");
  loadProjects();
  loadDeployments();
});
</script>

<style scoped>
.deployments-page {
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
  font-weight: 500;
}

.filter-card {
  margin-bottom: 20px;
}

.deployments-list {
  margin-bottom: 20px;
}

.text-muted {
  color: #909399;
}

.upload-info {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 20px;
}

.upload-info p {
  margin: 5px 0;
  color: #606266;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>
