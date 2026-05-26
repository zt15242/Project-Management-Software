<template>
  <div class="background-tasks-container">
    <el-card class="header-card">
      <div class="header-content">
        <h2>后台任务管理</h2>
        <div class="stats-row">
          <el-statistic title="总任务数" :value="stats.total" />
          <el-statistic title="运行中" :value="stats.running" />
          <el-statistic title="已暂停" :value="stats.paused" />
          <el-statistic title="已完成" :value="stats.completed" />
          <el-statistic title="失败" :value="stats.failed" />
        </div>
      </div>
    </el-card>

    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="任务类型">
          <el-select
            v-model="filterType"
            placeholder="全部"
            clearable
            @change="fetchTasks"
          >
            <el-option label="会议分析" value="meeting_analysis" />
            <el-option label="数据导出" value="data_export" />
            <el-option label="文件处理" value="file_processing" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="filterStatus"
            placeholder="全部"
            clearable
            @change="fetchTasks"
          >
            <el-option label="运行中" value="running" />
            <el-option label="已暂停" value="paused" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
            <el-option label="已停止" value="stopped" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchTasks" :icon="Refresh"
            >刷新</el-button
          >
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table :data="tasks" v-loading="loading" style="width: 100%">
        <el-table-column prop="task_name" label="任务名称" min-width="200" />

        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTaskTypeColor(row.task_type)">
              {{ getTaskTypeName(row.task_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="进度" width="150">
          <template #default="{ row }">
            <el-progress
              v-if="row.progress !== null && row.status === 'running'"
              :percentage="row.progress"
              :status="row.progress === 100 ? 'success' : undefined"
            />
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="CPU" width="80">
          <template #default="{ row }">
            <span v-if="row.cpu_percent !== null"
              >{{ row.cpu_percent.toFixed(1) }}%</span
            >
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="内存" width="100">
          <template #default="{ row }">
            <span v-if="row.memory_mb !== null"
              >{{ row.memory_mb.toFixed(0) }} MB</span
            >
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="耗时" width="120">
          <template #default="{ row }">
            <span v-if="row.duration !== null">{{
              formatDuration(row.duration)
            }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'running'"
              type="warning"
              size="small"
              @click="pauseTask(row.id)"
            >
              暂停
            </el-button>
            <el-button
              v-if="row.status === 'paused'"
              type="success"
              size="small"
              @click="resumeTask(row.id)"
            >
              继续
            </el-button>
            <el-button
              v-if="row.status === 'running' || row.status === 'paused'"
              type="danger"
              size="small"
              @click="stopTask(row.id)"
            >
              停止
            </el-button>
            <el-button
              v-if="
                row.status === 'completed' ||
                row.status === 'failed' ||
                row.status === 'stopped'
              "
              type="danger"
              size="small"
              plain
              @click="deleteTask(row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Refresh } from "@element-plus/icons-vue";
import axios from "axios";
import dayjs from "dayjs";

const tasks = ref([]);
const loading = ref(false);
const filterType = ref("");
const filterStatus = ref("");
const stats = ref({
  total: 0,
  running: 0,
  paused: 0,
  completed: 0,
  failed: 0,
});

let pollingTimer = null;

const fetchTasks = async () => {
  loading.value = true;
  try {
    const token = localStorage.getItem("token");
    const params = {};
    if (filterType.value) params.task_type = filterType.value;
    if (filterStatus.value) params.status = filterStatus.value;

    const response = await axios.get("/api/background-tasks/", {
      params,
      headers: { Authorization: `Bearer ${token}` },
    });
    tasks.value = response.data;
  } catch (error) {
    ElMessage.error("获取任务列表失败");
  } finally {
    loading.value = false;
  }
};

const fetchStats = async () => {
  try {
    const token = localStorage.getItem("token");
    const response = await axios.get("/api/background-tasks/stats/summary", {
      headers: { Authorization: `Bearer ${token}` },
    });
    stats.value = response.data;
  } catch (error) {
    console.error("获取统计信息失败:", error);
  }
};

const pauseTask = async (taskId) => {
  try {
    const token = localStorage.getItem("token");
    await axios.post(
      `/api/background-tasks/${taskId}/pause`,
      {},
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    ElMessage.success("任务已暂停");
    await fetchTasks();
    await fetchStats();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "暂停任务失败");
  }
};

const resumeTask = async (taskId) => {
  try {
    const token = localStorage.getItem("token");
    await axios.post(
      `/api/background-tasks/${taskId}/resume`,
      {},
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    ElMessage.success("任务已继续");
    await fetchTasks();
    await fetchStats();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "继续任务失败");
  }
};

const stopTask = async (taskId) => {
  try {
    await ElMessageBox.confirm("确定要停止这个任务吗？", "提示", {
      type: "warning",
    });

    const token = localStorage.getItem("token");
    await axios.post(
      `/api/background-tasks/${taskId}/stop`,
      {},
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    ElMessage.success("任务已停止");
    await fetchTasks();
    await fetchStats();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error(error.response?.data?.detail || "停止任务失败");
    }
  }
};

const deleteTask = async (taskId) => {
  try {
    await ElMessageBox.confirm("确定要删除这个任务记录吗？", "提示", {
      type: "warning",
    });

    const token = localStorage.getItem("token");
    await axios.delete(`/api/background-tasks/${taskId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    ElMessage.success("任务已删除");
    await fetchTasks();
    await fetchStats();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error(error.response?.data?.detail || "删除任务失败");
    }
  }
};

const getTaskTypeName = (type) => {
  const map = {
    meeting_analysis: "会议分析",
    data_export: "数据导出",
    file_processing: "文件处理",
  };
  return map[type] || type;
};

const getTaskTypeColor = (type) => {
  const map = {
    meeting_analysis: "primary",
    data_export: "success",
    file_processing: "warning",
  };
  return map[type] || "";
};

const getStatusText = (status) => {
  const map = {
    running: "运行中",
    paused: "已暂停",
    completed: "已完成",
    failed: "失败",
    stopped: "已停止",
  };
  return map[status] || status;
};

const getStatusType = (status) => {
  const map = {
    running: "primary",
    paused: "warning",
    completed: "success",
    failed: "danger",
    stopped: "info",
  };
  return map[status] || "";
};

const formatDuration = (seconds) => {
  if (seconds < 60) {
    return `${seconds.toFixed(0)}秒`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}分${secs}秒`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}小时${minutes}分`;
  }
};

const formatDateTime = (dateStr) => {
  return dayjs(dateStr).format("YYYY-MM-DD HH:mm:ss");
};

const startPolling = () => {
  // 每5秒刷新一次
  pollingTimer = setInterval(() => {
    fetchTasks();
    fetchStats();
  }, 5000);
};

const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer);
    pollingTimer = null;
  }
};

onMounted(() => {
  fetchTasks();
  fetchStats();
  startPolling();
});

onUnmounted(() => {
  stopPolling();
});
</script>

<style scoped>
.background-tasks-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.header-content h2 {
  margin: 0 0 20px 0;
  font-size: 24px;
  font-weight: 600;
}

.stats-row {
  display: flex;
  gap: 40px;
}

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}
</style>
