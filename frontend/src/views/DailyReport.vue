<template>
  <div class="daily-report">
    <div class="page-header">
      <h1>工作日报</h1>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog"
        >填写日报</el-button
      >
    </div>

    <!-- 日历视图 -->
    <el-card class="calendar-card">
      <template #header>
        <div class="calendar-card-header">
          <el-button :icon="ArrowLeft" circle @click="previousMonth" />
          <span class="current-month">{{ formatMonthYear(selectedDate) }}</span>
          <el-button :icon="ArrowRight" circle @click="nextMonth" />
        </div>
      </template>
      <el-calendar v-model="selectedDate">
        <template #date-cell="{ data }">
          <div
            class="calendar-day"
            @click="handleDateSingleClick(data.day)"
            @dblclick="handleDateDoubleClick(data.day)"
          >
            <div class="day-number">{{ data.day.split("-").slice(-1)[0] }}</div>
            <div
              class="day-reports"
              v-if="getReportsForDate(data.day).length > 0"
            >
              <el-badge
                :value="getTotalHours(data.day)"
                :max="99"
                class="hours-badge"
              >
                <el-icon><Clock /></el-icon>
              </el-badge>
              <div class="report-dots">
                <span
                  v-for="report in getReportsForDate(data.day).slice(0, 3)"
                  :key="report.id"
                  :class="['dot', `dot-${report.report_type}`]"
                  :title="report.content"
                ></span>
              </div>
            </div>
          </div>
        </template>
      </el-calendar>
    </el-card>

    <!-- 选中日期的日报列表 -->
    <el-card class="reports-card" v-if="selectedDateReports.length > 0">
      <template #header>
        <div class="card-header">
          <span>{{ formatDate(selectedDate) }} 的日报</span>
          <span class="total-hours"
            >总工时: {{ selectedDateTotalHours }}小时</span
          >
        </div>
      </template>
      <el-table :data="selectedDateReports" stripe border>
        <el-table-column label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.report_type)" size="small">
              {{ getTypeLabel(row.report_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="关联项" width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.task_title">{{ row.task_title }}</span>
            <span v-else-if="row.topic_title">{{ row.topic_title }}</span>
            <span v-else-if="row.project_name">{{ row.project_name }}</span>
            <span v-else style="color: #909399">-</span>
          </template>
        </el-table-column>
        <el-table-column label="工作内容" min-width="300" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.content }}
          </template>
        </el-table-column>
        <el-table-column label="工时" width="80" align="center">
          <template #default="{ row }"> {{ row.hours }}h </template>
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

    <!-- 创建/编辑日报对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        :model="reportForm"
        :rules="rules"
        ref="formRef"
        label-width="100px"
      >
        <el-form-item label="日期" prop="report_date">
          <el-date-picker
            v-model="reportForm.report_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            :disabled="isEdit"
          />
        </el-form-item>
        <el-form-item label="类型" prop="report_type">
          <el-radio-group
            v-model="reportForm.report_type"
            @change="handleTypeChange"
          >
            <el-radio label="task">任务</el-radio>
            <el-radio label="课题">课题</el-radio>
            <el-radio label="maintenance">日常运维</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item
          label="关联任务"
          prop="task_id"
          v-if="reportForm.report_type === 'task'"
        >
          <el-select
            v-model="reportForm.task_id"
            placeholder="选择任务"
            filterable
            style="width: 100%"
            @change="handleTaskChange"
          >
            <el-option
              v-for="task in availableTasks"
              :key="task.id"
              :label="`${task.title} (预计${task.estimated_hours}h, 已用${task.actual_hours}h)`"
              :value="task.id"
            />
          </el-select>
          <div v-if="selectedTask" class="task-info">
            <el-alert
              :title="`剩余工时: ${(
                selectedTask.estimated_hours - selectedTask.actual_hours
              ).toFixed(1)}小时`"
              type="info"
              :closable="false"
            />
          </div>
        </el-form-item>
        <el-form-item
          label="关联课题"
          prop="topic_id"
          v-if="reportForm.report_type === '课题'"
        >
          <el-select
            v-model="reportForm.topic_id"
            placeholder="选择课题"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="课题 in available课题s"
              :key="课题.id"
              :label="课题.title"
              :value="课题.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          label="关联项目"
          prop="project_id"
          v-if="reportForm.report_type === 'maintenance'"
        >
          <el-select
            v-model="reportForm.project_id"
            placeholder="选择项目"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="工作内容" prop="content">
          <el-input
            v-model="reportForm.content"
            type="textarea"
            :rows="4"
            placeholder="请描述今天的工作内容"
          />
        </el-form-item>
        <el-form-item label="工时(小时)" prop="hours">
          <el-input-number
            v-model="reportForm.hours"
            :min="0.5"
            :max="24"
            :step="0.5"
            :precision="1"
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
import { ref, reactive, onMounted, computed, watch } from "vue";
import { dailyReportAPI, taskAPI, topicAPI, projectAPI } from "@/api";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Plus,
  Edit,
  Delete,
  Clock,
  ArrowLeft,
  ArrowRight,
} from "@element-plus/icons-vue";
import dayjs from "dayjs";

const selectedDate = ref(new Date());
const reports = ref([]);
const tasks = ref([]);
const topics = ref([]);
const projects = ref([]);
const dialogVisible = ref(false);
const formRef = ref();
const submitting = ref(false);
const isEdit = ref(false);
const currentReport = ref(null);

const reportForm = reactive({
  report_date: new Date(),
  report_type: "task",
  project_id: "",
  task_id: "",
  topic_id: "",
  content: "",
  hours: 1,
});

const rules = {
  report_date: [{ required: true, message: "请选择日期", trigger: "change" }],
  report_type: [{ required: true, message: "请选择类型", trigger: "change" }],
  task_id: [
    {
      validator: (rule, value, callback) => {
        if (reportForm.report_type === "task" && !value) {
          callback(new Error("请选择任务"));
        } else {
          callback();
        }
      },
      trigger: "change",
    },
  ],
  topic_id: [
    {
      validator: (rule, value, callback) => {
        if (reportForm.report_type === "课题" && !value) {
          callback(new Error("请选择课题"));
        } else {
          callback();
        }
      },
      trigger: "change",
    },
  ],
  project_id: [
    {
      validator: (rule, value, callback) => {
        if (reportForm.report_type === "maintenance" && !value) {
          callback(new Error("请选择项目"));
        } else {
          callback();
        }
      },
      trigger: "change",
    },
  ],
  content: [{ required: true, message: "请输入工作内容", trigger: "blur" }],
  hours: [{ required: true, message: "请输入工时", trigger: "blur" }],
};

const dialogTitle = computed(() => (isEdit.value ? "编辑日报" : "填写日报"));

// 可用的任务（未完成的）
const availableTasks = computed(() => {
  return tasks.value.filter(
    (t) => t.status !== "completed" && t.status !== "cancelled"
  );
});

// 可用的课题（未关闭的）
const available课题s = computed(() => {
  return topics.value.filter((b) => b.status !== "closed");
});

// 选中的任务
const selectedTask = computed(() => {
  if (!reportForm.task_id) return null;
  return tasks.value.find((t) => t.id === reportForm.task_id);
});

// 选中日期的日报
const selectedDateReports = computed(() => {
  return getReportsForDate(dayjs(selectedDate.value).format("YYYY-MM-DD"));
});

// 选中日期的总工时
const selectedDateTotalHours = computed(() => {
  return selectedDateReports.value
    .reduce((sum, r) => sum + r.hours, 0)
    .toFixed(1);
});

const formatMonthYear = (date) => {
  return dayjs(date).format("YYYY年MM月");
};

const formatDate = (date) => {
  return dayjs(date).format("YYYY-MM-DD");
};

const getReportsForDate = (dateStr) => {
  return reports.value.filter((r) => {
    return dayjs(r.report_date).format("YYYY-MM-DD") === dateStr;
  });
};

const getTotalHours = (dateStr) => {
  const dayReports = getReportsForDate(dateStr);
  return dayReports.reduce((sum, r) => sum + r.hours, 0).toFixed(1);
};

const getTypeTag = (type) => {
  const tags = {
    task: "primary",
    课题: "danger",
    maintenance: "warning",
  };
  return tags[type] || "";
};

const getTypeLabel = (type) => {
  const labels = {
    task: "任务",
    课题: "课题",
    maintenance: "运维",
  };
  return labels[type] || type;
};

const fetchReports = async () => {
  try {
    // 获取当前月份的日报
    const startDate = dayjs(selectedDate.value).startOf("month").toISOString();
    const endDate = dayjs(selectedDate.value).endOf("month").toISOString();
    reports.value = await dailyReportAPI.getDailyReports({
      start_date: startDate,
      end_date: endDate,
    });
  } catch (error) {
    ElMessage.error("获取日报失败");
  }
};

const fetchTasks = async () => {
  try {
    tasks.value = await taskAPI.getTasks();
  } catch (error) {
    console.error("获取任务失败", error);
  }
};

const fetch课题s = async () => {
  try {
    topics.value = await topicAPI.getTopics();
  } catch (error) {
    console.error("获取课题失败", error);
  }
};

const fetchProjects = async () => {
  try {
    const data = await projectAPI.getProjects({ limit: 100 });
    projects.value = data.items || [];
  } catch (error) {
    console.error("获取项目失败", error);
  }
};

const handleDateSingleClick = (dateStr) => {
  // 单击只选中日期
  selectedDate.value = new Date(dateStr);
};

const handleDateDoubleClick = (dateStr) => {
  // 双击弹出创建日报对话框
  selectedDate.value = new Date(dateStr);
  isEdit.value = false;
  Object.assign(reportForm, {
    report_date: new Date(dateStr),
    report_type: "task",
    project_id: "",
    task_id: "",
    topic_id: "",
    content: "",
    hours: 1,
  });
  dialogVisible.value = true;
};

const showCreateDialog = () => {
  isEdit.value = false;
  Object.assign(reportForm, {
    report_date: selectedDate.value,
    report_type: "task",
    project_id: "",
    task_id: "",
    topic_id: "",
    content: "",
    hours: 1,
  });
  dialogVisible.value = true;
};

const handleEdit = (report) => {
  isEdit.value = true;
  currentReport.value = report;
  Object.assign(reportForm, {
    report_date: new Date(report.report_date),
    report_type: report.report_type,
    project_id: report.project_id || "",
    task_id: report.task_id || "",
    topic_id: report.topic_id || "",
    content: report.content,
    hours: report.hours,
  });
  dialogVisible.value = true;
};

const handleTypeChange = () => {
  reportForm.project_id = "";
  reportForm.task_id = "";
  reportForm.topic_id = "";
};

const handleTaskChange = () => {
  // 任务改变时可以自动填充一些信息
};

const handleSubmit = async () => {
  const valid = await formRef.value.validate();
  if (!valid) return;

  submitting.value = true;
  try {
    const data = {
      report_date: dayjs(reportForm.report_date).toISOString(),
      report_type: reportForm.report_type,
      content: reportForm.content,
      hours: reportForm.hours,
    };

    if (reportForm.report_type === "task") {
      data.task_id = reportForm.task_id;
    } else if (reportForm.report_type === "课题") {
      data.topic_id = reportForm.topic_id;
    } else if (reportForm.report_type === "maintenance") {
      data.project_id = reportForm.project_id;
    }

    if (isEdit.value) {
      await dailyReportAPI.updateDailyReport(currentReport.value.id, {
        content: data.content,
        hours: data.hours,
      });
      ElMessage.success("日报更新成功");
    } else {
      await dailyReportAPI.createDailyReport(data);
      ElMessage.success("日报创建成功");
    }

    dialogVisible.value = false;
    fetchReports();
    fetchTasks(); // 刷新任务列表以更新工时
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "操作失败");
  } finally {
    submitting.value = false;
  }
};

const handleDelete = async (report) => {
  try {
    await ElMessageBox.confirm("确定要删除这条日报吗？", "提示", {
      type: "warning",
    });
    await dailyReportAPI.deleteDailyReport(report.id);
    ElMessage.success("删除成功");
    fetchReports();
    fetchTasks(); // 刷新任务列表以更新工时
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
};

const resetForm = () => {
  formRef.value?.resetFields();
};

// 月份导航函数
const previousMonth = () => {
  selectedDate.value = dayjs(selectedDate.value).subtract(1, "month").toDate();
};

const nextMonth = () => {
  selectedDate.value = dayjs(selectedDate.value).add(1, "month").toDate();
};

// 监听selectedDate变化，当月份改变时重新加载数据
watch(selectedDate, (newDate, oldDate) => {
  // 检查月份是否改变
  const newMonth = dayjs(newDate).format("YYYY-MM");
  const oldMonth = oldDate ? dayjs(oldDate).format("YYYY-MM") : null;

  if (newMonth !== oldMonth) {
    console.log(`月份切换: ${oldMonth} -> ${newMonth}`);
    fetchReports();
  }
});

onMounted(() => {
  fetchReports();
  fetchTasks();
  fetch课题s();
  fetchProjects();
});
</script>

<style scoped>
.daily-report {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.calendar-card {
  margin-bottom: 20px;
}

.calendar-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.current-month {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.calendar-header {
  text-align: center;
  font-size: 18px;
  font-weight: bold;
}

.calendar-day {
  height: 100%;
  padding: 5px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.calendar-day:hover {
  background-color: #f5f7fa;
}

.day-number {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 5px;
}

.day-reports {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.hours-badge {
  font-size: 12px;
}

.report-dots {
  display: flex;
  gap: 3px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.dot-task {
  background-color: #409eff;
}

.dot-课题 {
  background-color: #f56c6c;
}

.dot-maintenance {
  background-color: #e6a23c;
}

.reports-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.total-hours {
  color: #409eff;
  font-size: 14px;
}

.task-info {
  margin-top: 10px;
}

:deep(.el-calendar-table .el-calendar-day) {
  height: 80px;
  padding: 0;
}

:deep(.el-calendar-table td.is-selected) {
  background-color: #ecf5ff;
}

:deep(.el-calendar-table td.is-today) {
  color: #409eff;
}
</style>
