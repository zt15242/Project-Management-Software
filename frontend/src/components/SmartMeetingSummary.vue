<template>
  <div class="smart-summary-container">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>AI正在生成智能纪要...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <el-alert type="error" :title="error" :closable="false" />
    </div>

    <!-- 智能纪要内容 -->
    <div v-else-if="summaryData" class="summary-content">
      <!-- 头部信息 -->
      <div class="summary-header">
        <h1 class="meeting-title">{{ summaryData.meeting_title }}</h1>
        <div class="meeting-meta">
          <span v-if="summaryData.meeting_date" class="meta-item">
            <el-icon><Calendar /></el-icon>
            {{ summaryData.meeting_date }}
          </span>
          <span
            v-if="summaryData.participants && summaryData.participants.length"
            class="meta-item"
          >
            <el-icon><User /></el-icon>
            {{ summaryData.participants.join("、") }}
          </span>
          <span v-if="summaryData.duration" class="meta-item">
            <el-icon><Clock /></el-icon>
            {{ summaryData.duration }}
          </span>
        </div>
      </div>

      <!-- Tab切换 -->
      <el-tabs v-model="activeTab" class="summary-tabs">
        <!-- 核心纪要 -->
        <el-tab-pane label="核心纪要" name="core">
          <!-- 会议概览 -->
          <div class="section">
            <h2 class="section-title">会议概览</h2>
            <div class="summary-box">
              {{ summaryData.summary }}
            </div>
          </div>

          <!-- 详细内容摘要 -->
          <div
            v-if="summaryData.key_points && summaryData.key_points.length"
            class="section"
          >
            <h2 class="section-title">详细内容摘要</h2>
            <div class="key-points-grid">
              <div
                v-for="(point, index) in summaryData.key_points"
                :key="index"
                class="key-point-card"
              >
                <div class="card-icon">{{ point.icon || "📋" }}</div>
                <div class="card-content">
                  <h3 class="card-title">{{ point.title }}</h3>
                  <p class="card-text">{{ point.content }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- 关键结论 -->
          <div
            v-if="summaryData.conclusions && summaryData.conclusions.length"
            class="section"
          >
            <h2 class="section-title">
              <el-icon class="title-icon"><Check /></el-icon>
              关键结论
            </h2>
            <div class="conclusions-container">
              <div
                v-for="(conclusion, index) in summaryData.conclusions"
                :key="index"
                class="conclusion-item"
              >
                <div class="conclusion-header">
                  <el-icon class="check-icon"><CircleCheck /></el-icon>
                  <h3>{{ conclusion.title }}</h3>
                </div>
                <p class="conclusion-content">{{ conclusion.content }}</p>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 讨论主题 -->
        <el-tab-pane
          v-if="
            summaryData.discussion_topics &&
            summaryData.discussion_topics.length
          "
          label="讨论主题"
          name="discussion"
        >
          <div
            v-for="(topic, index) in summaryData.discussion_topics"
            :key="index"
            class="discussion-card"
          >
            <h3 class="discussion-title">{{ topic.topic }}</h3>
            <p class="discussion-summary">{{ topic.summary }}</p>
            <div
              v-if="topic.decisions && topic.decisions.length"
              class="decisions"
            >
              <h4>决策：</h4>
              <ul>
                <li v-for="(decision, dIndex) in topic.decisions" :key="dIndex">
                  {{ decision }}
                </li>
              </ul>
            </div>
          </div>
        </el-tab-pane>

        <!-- 待办事项 -->
        <el-tab-pane
          v-if="summaryData.action_items && summaryData.action_items.length"
          label="待办事项/行动项"
          name="actions"
        >
          <div class="action-items-container">
            <div
              v-for="(item, index) in summaryData.action_items"
              :key="index"
              class="action-item"
              :class="`priority-${item.priority || 'medium'}`"
            >
              <div class="action-header">
                <el-tag
                  :type="getPriorityType(item.priority)"
                  size="small"
                  class="priority-tag"
                >
                  {{ getPriorityText(item.priority) }}
                </el-tag>
                <span class="action-task">{{ item.task }}</span>
                <el-button
                  type="primary"
                  size="small"
                  @click="createTaskFromAction(item)"
                  class="create-task-btn"
                >
                  <el-icon><Plus /></el-icon>
                  创建任务
                </el-button>
              </div>
              <div class="action-meta">
                <span v-if="item.owner" class="action-owner">
                  <el-icon><User /></el-icon>
                  {{ item.owner }}
                </span>
                <span v-if="item.deadline" class="action-deadline">
                  <el-icon><Calendar /></el-icon>
                  {{ item.deadline }}
                </span>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 风险与缓解 -->
        <el-tab-pane
          v-if="summaryData.risks && summaryData.risks.length"
          label="风险与缓解"
          name="risks"
        >
          <div class="risks-container">
            <div
              v-for="(risk, index) in summaryData.risks"
              :key="index"
              class="risk-card"
            >
              <div class="risk-header">
                <el-icon class="risk-icon"><WarningFilled /></el-icon>
                <h3>{{ risk.risk }}</h3>
              </div>
              <div class="risk-content">
                <div class="risk-item">
                  <strong>影响：</strong>
                  <span>{{ risk.impact }}</span>
                </div>
                <div class="risk-item">
                  <strong>缓解措施：</strong>
                  <span>{{ risk.mitigation }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 下一步行动 -->
        <el-tab-pane
          v-if="summaryData.next_steps && summaryData.next_steps.length"
          label="下一步行动"
          name="next"
        >
          <div class="next-steps-container">
            <div
              v-for="(step, index) in summaryData.next_steps"
              :key="index"
              class="next-step-item"
            >
              <div class="step-number">{{ index + 1 }}</div>
              <div class="step-content">{{ step }}</div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import {
  Loading,
  Calendar,
  User,
  Clock,
  Check,
  CircleCheck,
  WarningFilled,
  Plus,
} from "@element-plus/icons-vue";

const props = defineProps({
  summaryContent: {
    type: String,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["createTask"]);

const activeTab = ref("core");
const summaryData = ref(null);
const error = ref(null);

// 解析JSON数据
const parseSummaryData = () => {
  try {
    const parsed = JSON.parse(props.summaryContent);
    if (parsed.error) {
      error.value = parsed.error;
    } else {
      summaryData.value = parsed;
    }
  } catch (e) {
    error.value = "智能纪要数据格式错误";
    console.error("解析智能纪要失败:", e);
  }
};

// 获取优先级类型
const getPriorityType = (priority) => {
  const typeMap = {
    high: "danger",
    medium: "warning",
    low: "info",
  };
  return typeMap[priority] || "info";
};

// 获取优先级文本
const getPriorityText = (priority) => {
  const textMap = {
    high: "高优先级",
    medium: "中优先级",
    low: "低优先级",
  };
  return textMap[priority] || "普通";
};

// 从待办事项创建任务
const createTaskFromAction = (actionItem) => {
  emit("createTask", actionItem);
};

onMounted(() => {
  if (props.summaryContent && !props.loading) {
    parseSummaryData();
  }
});

// 监听summaryContent变化
import { watch } from "vue";
watch(
  () => props.summaryContent,
  (newVal) => {
    if (newVal && !props.loading) {
      parseSummaryData();
    }
  }
);
</script>

<style scoped>
.smart-summary-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 500px;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.loading-state p {
  margin-top: 20px;
  font-size: 16px;
  color: #666;
}

/* 头部样式 */
.summary-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px;
  border-radius: 12px;
  color: white;
  margin-bottom: 30px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.meeting-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 20px 0;
}

.meeting-meta {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  opacity: 0.95;
}

/* Tab样式 */
.summary-tabs {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

/* 章节样式 */
.section {
  margin-bottom: 40px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  color: #67c23a;
  font-size: 28px;
}

/* 概览框 */
.summary-box {
  background: linear-gradient(135deg, #f5f7fa 0%, #e8eaf0 100%);
  padding: 25px;
  border-radius: 8px;
  font-size: 16px;
  line-height: 1.8;
  color: #606266;
  border-left: 4px solid #409eff;
}

/* 要点卡片网格 */
.key-points-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.key-point-card {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s;
  display: flex;
  gap: 15px;
}

.key-point-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.card-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 10px 0;
  color: #303133;
}

.card-text {
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
  margin: 0;
}

/* 结论样式 */
.conclusions-container {
  background: #f0f9ff;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #b3d8ff;
}

.conclusion-item {
  margin-bottom: 20px;
}

.conclusion-item:last-child {
  margin-bottom: 0;
}

.conclusion-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.check-icon {
  color: #67c23a;
  font-size: 20px;
}

.conclusion-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.conclusion-content {
  margin: 0;
  padding-left: 30px;
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
}

/* 讨论主题卡片 */
.discussion-card {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 25px;
  margin-bottom: 20px;
}

.discussion-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 15px 0;
  color: #303133;
}

.discussion-summary {
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
  margin: 0 0 15px 0;
}

.decisions h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 10px 0;
  color: #409eff;
}

.decisions ul {
  margin: 0;
  padding-left: 20px;
}

.decisions li {
  font-size: 14px;
  line-height: 1.8;
  color: #606266;
}

/* 待办事项 */
.action-items-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.action-item {
  background: white;
  border-left: 4px solid #909399;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.action-item.priority-high {
  border-left-color: #f56c6c;
}

.action-item.priority-medium {
  border-left-color: #e6a23c;
}

.action-item.priority-low {
  border-left-color: #909399;
}

.action-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.priority-tag {
  flex-shrink: 0;
}

.action-task {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  flex: 1;
}

.create-task-btn {
  margin-left: auto;
  flex-shrink: 0;
}

.action-meta {
  display: flex;
  gap: 20px;
  font-size: 14px;
  color: #909399;
}

.action-owner,
.action-deadline {
  display: flex;
  align-items: center;
  gap: 5px;
}

/* 风险卡片 */
.risks-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.risk-card {
  background: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 8px;
  padding: 20px;
}

.risk-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.risk-icon {
  color: #f56c6c;
  font-size: 24px;
}

.risk-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.risk-content {
  padding-left: 34px;
}

.risk-item {
  margin-bottom: 10px;
  font-size: 14px;
  line-height: 1.6;
}

.risk-item:last-child {
  margin-bottom: 0;
}

.risk-item strong {
  color: #606266;
  margin-right: 8px;
}

.risk-item span {
  color: #909399;
}

/* 下一步行动 */
.next-steps-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.next-step-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  background: white;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.step-number {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 16px;
}

.step-content {
  flex: 1;
  font-size: 15px;
  line-height: 1.8;
  color: #606266;
  padding-top: 6px;
}
</style>
