<template>
  <div class="dashboard">
    <h1 class="page-title">数据看板</h1>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#409EFF"><Folder /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ totalProjects }}</div>
              <div class="stat-label">项目总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#67C23A"><List /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ totalTasks }}</div>
              <div class="stat-label">任务总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#F56C6C"><Warning /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ totalTopics }}</div>
              <div class="stat-label">课题总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#E6A23C"><User /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ totalMembers }}</div>
              <div class="stat-label">团队成员</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>项目统计</span>
            </div>
          </template>
          <div class="project-list">
            <div
              v-for="stat in statistics"
              :key="stat.project_id"
              class="project-stat-item"
            >
              <div class="project-name">{{ stat.project_name }}</div>
              <div class="progress-info">
                <span>任务完成率</span>
                <span class="percent">{{ stat.task_completion_rate }}%</span>
              </div>
              <el-progress
                :percentage="stat.task_completion_rate"
                :color="getProgressColor(stat.task_completion_rate)"
              />
              <div class="stat-details">
                <span
                  >任务: {{ stat.completed_tasks }}/{{ stat.total_tasks }}</span
                >
                <span
                  >课题: {{ stat.open_topics }}/{{ stat.total_topics }}</span
                >
                <span>成员: {{ stat.team_size }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>课题率统计</span>
            </div>
          </template>
          <div ref="bugChartRef" style="height: 400px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 任务看板 -->
    <el-row :gutter="20" class="kanban-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>任务看板</span>
              <el-button type="primary" size="small" @click="goToTasks"
                >查看全部</el-button
              >
            </div>
          </template>
          <el-row :gutter="15" class="kanban-container">
            <el-col :span="6">
              <div class="kanban-column">
                <div class="column-header todo">
                  <span>待办</span>
                  <el-badge :value="todoTasks.length" class="badge" />
                </div>
                <div class="kanban-cards">
                  <div
                    v-for="task in todoTasks"
                    :key="task.id"
                    class="kanban-card"
                    @click="viewTask(task)"
                  >
                    <div class="card-title">{{ task.title }}</div>
                    <div class="card-meta">
                      <el-tag
                        size="small"
                        :type="getPriorityType(task.priority)"
                        >{{ getPriorityLabel(task.priority) }}</el-tag
                      >
                      <span class="card-project">{{
                        getProjectName(task.project_id)
                      }}</span>
                    </div>
                    <div class="card-footer">
                      <span v-if="task.assigned_to" class="assignee">{{
                        getUserName(task.assigned_to)
                      }}</span>
                      <span v-if="task.due_date" class="due-date">{{
                        formatDate(task.due_date)
                      }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="kanban-column">
                <div class="column-header in-progress">
                  <span>进行中</span>
                  <el-badge :value="inProgressTasks.length" class="badge" />
                </div>
                <div class="kanban-cards">
                  <div
                    v-for="task in inProgressTasks"
                    :key="task.id"
                    class="kanban-card"
                    @click="viewTask(task)"
                  >
                    <div class="card-title">{{ task.title }}</div>
                    <div class="card-meta">
                      <el-tag
                        size="small"
                        :type="getPriorityType(task.priority)"
                        >{{ getPriorityLabel(task.priority) }}</el-tag
                      >
                      <span class="card-project">{{
                        getProjectName(task.project_id)
                      }}</span>
                    </div>
                    <div class="card-footer">
                      <span v-if="task.assigned_to" class="assignee">{{
                        getUserName(task.assigned_to)
                      }}</span>
                      <span v-if="task.due_date" class="due-date">{{
                        formatDate(task.due_date)
                      }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="kanban-column">
                <div class="column-header completed">
                  <span>已完成</span>
                  <el-badge :value="completedTasks.length" class="badge" />
                </div>
                <div class="kanban-cards">
                  <div
                    v-for="task in completedTasks"
                    :key="task.id"
                    class="kanban-card"
                    @click="viewTask(task)"
                  >
                    <div class="card-title">{{ task.title }}</div>
                    <div class="card-meta">
                      <el-tag
                        size="small"
                        :type="getPriorityType(task.priority)"
                        >{{ getPriorityLabel(task.priority) }}</el-tag
                      >
                      <span class="card-project">{{
                        getProjectName(task.project_id)
                      }}</span>
                    </div>
                    <div class="card-footer">
                      <span v-if="task.assigned_to" class="assignee">{{
                        getUserName(task.assigned_to)
                      }}</span>
                      <span v-if="task.due_date" class="due-date">{{
                        formatDate(task.due_date)
                      }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="kanban-column">
                <div class="column-header cancelled">
                  <span>已取消</span>
                  <el-badge :value="cancelledTasks.length" class="badge" />
                </div>
                <div class="kanban-cards">
                  <div
                    v-for="task in cancelledTasks"
                    :key="task.id"
                    class="kanban-card"
                    @click="viewTask(task)"
                  >
                    <div class="card-title">{{ task.title }}</div>
                    <div class="card-meta">
                      <el-tag
                        size="small"
                        :type="getPriorityType(task.priority)"
                        >{{ getPriorityLabel(task.priority) }}</el-tag
                      >
                      <span class="card-project">{{
                        getProjectName(task.project_id)
                      }}</span>
                    </div>
                    <div class="card-footer">
                      <span v-if="task.assigned_to" class="assignee">{{
                        getUserName(task.assigned_to)
                      }}</span>
                      <span v-if="task.due_date" class="due-date">{{
                        formatDate(task.due_date)
                      }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 课题看板 -->
    <el-row :gutter="20" class="kanban-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>课题看板</span>
              <el-button type="primary" size="small" @click="goToTopics"
                >查看全部</el-button
              >
            </div>
          </template>
          <el-row :gutter="15" class="kanban-container">
            <el-col :span="8">
              <div class="kanban-column">
                <div class="column-header bug-open">
                  <span>待修复</span>
                  <el-badge :value="openTopics.length" class="badge" />
                </div>
                <div class="kanban-cards">
                  <div
                    v-for="bug in openTopics"
                    :key="bug.id"
                    class="kanban-card bug-card"
                    @click="viewTopic(bug)"
                  >
                    <div class="card-title">{{ bug.title }}</div>
                    <div class="card-meta">
                      <el-tag
                        size="small"
                        :type="getSeverityType(bug.severity)"
                        >{{ getSeverityLabel(bug.severity) }}</el-tag
                      >
                      <span class="card-project">{{
                        getProjectName(bug.project_id)
                      }}</span>
                    </div>
                    <div class="card-footer">
                      <span v-if="bug.assigned_to" class="assignee">{{
                        getUserName(bug.assigned_to)
                      }}</span>
                      <span v-if="bug.created_at" class="created-date">{{
                        formatDate(bug.created_at)
                      }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="kanban-column">
                <div class="column-header bug-fixing">
                  <span>修复中</span>
                  <el-badge :value="fixingTopics.length" class="badge" />
                </div>
                <div class="kanban-cards">
                  <div
                    v-for="bug in fixingTopics"
                    :key="bug.id"
                    class="kanban-card bug-card"
                    @click="viewTopic(bug)"
                  >
                    <div class="card-title">{{ bug.title }}</div>
                    <div class="card-meta">
                      <el-tag
                        size="small"
                        :type="getSeverityType(bug.severity)"
                        >{{ getSeverityLabel(bug.severity) }}</el-tag
                      >
                      <span class="card-project">{{
                        getProjectName(bug.project_id)
                      }}</span>
                    </div>
                    <div class="card-footer">
                      <span v-if="bug.assigned_to" class="assignee">{{
                        getUserName(bug.assigned_to)
                      }}</span>
                      <span v-if="bug.created_at" class="created-date">{{
                        formatDate(bug.created_at)
                      }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="kanban-column">
                <div class="column-header bug-closed">
                  <span>已关闭</span>
                  <el-badge :value="closedTopics.length" class="badge" />
                </div>
                <div class="kanban-cards">
                  <div
                    v-for="bug in closedTopics"
                    :key="bug.id"
                    class="kanban-card bug-card"
                    @click="viewTopic(bug)"
                  >
                    <div class="card-title">{{ bug.title }}</div>
                    <div class="card-meta">
                      <el-tag
                        size="small"
                        :type="getSeverityType(bug.severity)"
                        >{{ getSeverityLabel(bug.severity) }}</el-tag
                      >
                      <span class="card-project">{{
                        getProjectName(bug.project_id)
                      }}</span>
                    </div>
                    <div class="card-footer">
                      <span v-if="bug.assigned_to" class="assignee">{{
                        getUserName(bug.assigned_to)
                      }}</span>
                      <span v-if="bug.resolved_at" class="resolved-date">{{
                        formatDate(bug.resolved_at)
                      }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { statisticsAPI, taskAPI, topicAPI, projectAPI, userAPI } from "@/api";
import { Folder, List, User, Warning } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import * as echarts from "echarts";
import dayjs from "dayjs";

const router = useRouter();
const statistics = ref([]);
const bugChartRef = ref();
const tasks = ref([]);
const topics = ref([]);
const projects = ref([]);
const users = ref([]);

const totalProjects = computed(() => statistics.value.length);
const totalTasks = computed(() =>
  statistics.value.reduce((sum, s) => sum + s.total_tasks, 0)
);
const totalTopics = computed(() =>
  statistics.value.reduce((sum, s) => sum + s.total_topics, 0)
);
const totalMembers = computed(() => {
  const members = new Set();
  statistics.value.forEach((s) => members.add(s.team_size));
  return statistics.value.reduce((sum, s) => sum + s.team_size, 0);
});

// 任务分类
const todoTasks = computed(() =>
  tasks.value.filter((t) => t.status === "todo").slice(0, 5)
);
const inProgressTasks = computed(() =>
  tasks.value.filter((t) => t.status === "in_progress").slice(0, 5)
);
const completedTasks = computed(() =>
  tasks.value.filter((t) => t.status === "completed").slice(0, 5)
);
const cancelledTasks = computed(() =>
  tasks.value.filter((t) => t.status === "cancelled").slice(0, 5)
);

// Bug分类
const openTopics = computed(() =>
  topics.value.filter((b) => b.status === "open").slice(0, 5)
);
const fixingTopics = computed(() =>
  topics.value.filter((b) => b.status === "fixing").slice(0, 5)
);
const closedTopics = computed(() =>
  topics.value.filter((b) => b.status === "closed").slice(0, 5)
);

const getProgressColor = (percentage) => {
  if (percentage < 30) return "#F56C6C";
  if (percentage < 70) return "#E6A23C";
  return "#67C23A";
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

const getSeverityType = (severity) => {
  const types = {
    low: "info",
    medium: "warning",
    high: "danger",
    critical: "danger",
  };
  return types[severity] || "";
};

const getSeverityLabel = (severity) => {
  const labels = {
    low: "低",
    medium: "中",
    high: "高",
    critical: "严重",
  };
  return labels[severity] || severity;
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

const formatDate = (date) => {
  return dayjs(date).format("MM-DD");
};

const fetchStatistics = async () => {
  try {
    statistics.value = await statisticsAPI.getAllStatistics();
    renderBugChart();
  } catch (error) {
    console.error("获取统计数据失败", error);
  }
};

const fetchTasks = async () => {
  try {
    tasks.value = await taskAPI.getTasks();
  } catch (error) {
    console.error("获取任务失败", error);
  }
};

const fetchTopics = async () => {
  try {
    topics.value = await topicAPI.getTopics();
  } catch (error) {
    console.error("获取Bug失败", error);
  }
};

const fetchProjects = async () => {
  try {
    const data = await projectAPI.getProjects();
    projects.value = data.items || [];
  } catch (error) {
    console.error("获取项目失败", error);
  }
};

const fetchUsers = async () => {
  try {
    users.value = await userAPI.getUsers();
  } catch (error) {
    console.error("获取用户失败", error);
  }
};

const renderBugChart = () => {
  if (!bugChartRef.value) return;

  const chart = echarts.init(bugChartRef.value);
  const option = {
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "shadow",
      },
    },
    legend: {
      data: ["打开的课题", "已关闭课题", "课题率"],
    },
    xAxis: {
      type: "category",
      data: statistics.value.map((s) => s.project_name),
    },
    yAxis: [
      {
        type: "value",
        name: "课题数量",
      },
      {
        type: "value",
        name: "课题率(%)",
        max: 100,
      },
    ],
    series: [
      {
        name: "打开的课题",
        type: "bar",
        data: statistics.value.map((s) => s.open_topics),
        itemStyle: { color: "#F56C6C" },
      },
      {
        name: "已关闭课题",
        type: "bar",
        data: statistics.value.map((s) => s.closed_topics),
        itemStyle: { color: "#67C23A" },
      },
      {
        name: "课题率",
        type: "line",
        yAxisIndex: 1,
        data: statistics.value.map((s) => s.topic_rate),
        itemStyle: { color: "#409EFF" },
      },
    ],
  };

  chart.setOption(option);
};

const viewTask = (task) => {
  ElMessage.info(`查看任务: ${task.title}`);
  // 可以添加跳转到任务详情页的逻辑
};

const viewTopic = (topic) => {
  ElMessage.info(`查看课题: ${bug.title}`);
  // 可以添加跳转到Bug详情页的逻辑
};

const goToTasks = () => {
  router.push("/tasks");
};

const goToTopics = () => {
  router.push("/topics");
};

onMounted(() => {
  fetchStatistics();
  fetchTasks();
  fetchTopics();
  fetchProjects();
  fetchUsers();
});
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.page-title {
  margin-bottom: 20px;
  color: #333;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  font-size: 48px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  color: #999;
  margin-top: 5px;
}

.charts-row {
  margin-top: 20px;
}

.card-header {
  font-weight: bold;
}

.project-list {
  max-height: 400px;
  overflow-y: auto;
}

.project-stat-item {
  padding: 15px 0;
  border-bottom: 1px solid #eee;
}

.project-stat-item:last-child {
  border-bottom: none;
}

.project-name {
  font-weight: bold;
  margin-bottom: 10px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: 14px;
  color: #666;
}

.percent {
  font-weight: bold;
  color: #409eff;
}

.stat-details {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 13px;
  color: #999;
}

/* 看板样式 */
.kanban-row {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.kanban-container {
  min-height: 400px;
}

.kanban-column {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 10px;
  min-height: 400px;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;
  font-weight: bold;
  color: white;
}

.column-header.todo {
  background: #909399;
}

.column-header.in-progress {
  background: #e6a23c;
}

.column-header.completed {
  background: #67c23a;
}

.column-header.cancelled {
  background: #f56c6c;
}

.column-header.bug-open {
  background: #f56c6c;
}

.column-header.bug-fixing {
  background: #e6a23c;
}

.column-header.bug-closed {
  background: #67c23a;
}

.column-header .badge {
  margin-left: 8px;
}

.kanban-cards {
  max-height: 350px;
  overflow-y: auto;
}

.kanban-card {
  background: white;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.kanban-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.kanban-card:last-child {
  margin-bottom: 0;
}

.card-title {
  font-weight: 500;
  margin-bottom: 8px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.card-project {
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
}

.assignee {
  display: flex;
  align-items: center;
}

.assignee::before {
  content: "👤";
  margin-right: 4px;
}

.due-date,
.created-date,
.resolved-date {
  font-size: 11px;
}

.due-date::before {
  content: "📅";
  margin-right: 4px;
}

.created-date::before {
  content: "🕐";
  margin-right: 4px;
}

.resolved-date::before {
  content: "✅";
  margin-right: 4px;
}

.bug-card {
  border-left: 3px solid #f56c6c;
}

/* 滚动条样式 */
.kanban-cards::-webkit-scrollbar {
  width: 6px;
}

.kanban-cards::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.kanban-cards::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}
</style>
```
