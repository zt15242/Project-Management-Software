<template>
  <div class="bi-management">
    <div class="page-header">
      <h1>BI商业智能</h1>
      <el-select
        v-model="selectedProjectId"
        placeholder="选择项目"
        style="width: 300px"
        @change="handleProjectChange"
      >
        <el-option
          v-for="project in projects"
          :key="project.id"
          :label="project.name"
          :value="project.id"
        />
      </el-select>
    </div>

    <el-tabs v-model="activeTab" class="bi-tabs">
      <el-tab-pane label="数据源" name="datasources">
        <DataSourceManagement :project-id="selectedProjectId" />
      </el-tab-pane>
      <el-tab-pane label="报表" name="reports">
        <ReportManagement :project-id="selectedProjectId" />
      </el-tab-pane>
      <el-tab-pane label="仪表板" name="dashboards">
        <DashboardManagement :project-id="selectedProjectId" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { projectAPI } from "@/api";
import { ElMessage } from "element-plus";
import DataSourceManagement from "./DataSourceManagement.vue";
import ReportManagement from "./ReportManagement.vue";
import DashboardManagement from "./DashboardManagement.vue";

const projects = ref([]);
const selectedProjectId = ref("");
const activeTab = ref("datasources");

const fetchProjects = async () => {
  try {
    const data = await projectAPI.getProjects({ limit: 100 });
    projects.value = data.items || [];
    if (projects.value.length > 0) {
      selectedProjectId.value = projects.value[0].id;
    }
  } catch (error) {
    ElMessage.error("获取项目列表失败");
  }
};

const handleProjectChange = () => {
  // 项目切换后，子组件会自动刷新
};

onMounted(() => {
  fetchProjects();
});
</script>

<style scoped>
.bi-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.bi-tabs {
  margin-top: 20px;
}
</style>

