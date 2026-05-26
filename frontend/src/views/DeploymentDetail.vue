<template>
  <div class="deployment-detail-page">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="router.back()" text>
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h1>{{ deployment?.title }}</h1>
        <el-tag
          :type="
            deployment?.deployment_type === 'logic_code' ? 'primary' : 'success'
          "
        >
          {{
            deployment?.deployment_type === "logic_code"
              ? "逻辑代码包"
              : "页面代码包"
          }}
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showUploadDialog">
          <el-icon><Upload /></el-icon>
          上传新版本
        </el-button>
        <el-button @click="loadDeployment">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <el-card class="info-card" v-loading="loading">
      <template #header>
        <span>基本信息</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="包名称">{{
          deployment?.title
        }}</el-descriptions-item>
        <el-descriptions-item label="发布类型">
          <el-tag
            :type="
              deployment?.deployment_type === 'logic_code'
                ? 'primary'
                : 'success'
            "
          >
            {{
              deployment?.deployment_type === "logic_code"
                ? "逻辑代码包"
                : "页面代码包"
            }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="当前版本">
          <el-tag v-if="deployment?.current_version > 0" type="info"
            >v{{ deployment?.current_version }}</el-tag
          >
          <span v-else class="text-muted">无版本</span>
        </el-descriptions-item>
        <el-descriptions-item label="版本数量">{{
          deployment?.versions?.length || 0
        }}</el-descriptions-item>

        <!-- 新增：环境配置信息 -->
        <el-descriptions-item
          label="环境配置"
          v-if="deployment?.environment_id"
        >
          {{ environmentName || "加载中..." }}
        </el-descriptions-item>
        <el-descriptions-item label="包路径" v-if="deployment?.package_path">
          <el-tag type="info">{{ deployment?.package_path }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item
          label="远程包ID"
          v-if="deployment?.remote_package_id"
        >
          <el-tag type="success">{{ deployment?.remote_package_id }}</el-tag>
        </el-descriptions-item>

        <el-descriptions-item label="创建时间">{{
          formatDate(deployment?.created_at)
        }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{
          formatDate(deployment?.updated_at)
        }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{
          deployment?.description || "-"
        }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 版本列表 -->
    <el-card class="versions-card">
      <template #header>
        <span>版本历史</span>
      </template>

      <el-timeline v-if="sortedVersions.length > 0">
        <el-timeline-item
          v-for="version in sortedVersions"
          :key="version.version"
          :timestamp="formatDate(version.uploaded_at)"
          placement="top"
        >
          <el-card>
            <template #header>
              <div class="version-header">
                <div class="version-title">
                  <el-tag type="info" size="large"
                    >版本 {{ version.version }}</el-tag
                  >
                  <el-tag
                    :type="getStatusType(version.status)"
                    size="large"
                    style="margin-left: 10px"
                  >
                    {{ getStatusText(version.status) }}
                  </el-tag>
                  <!-- 显示分析进度 -->
                  <span
                    v-if="version.analysis_progress"
                    style="margin-left: 10px"
                  >
                    <el-tag type="info">
                      {{ version.analysis_progress }}
                      <span v-if="version.analysis_percentage !== undefined">
                        ({{ version.analysis_percentage }}%)</span
                      >
                    </el-tag>
                  </span>
                  <span v-if="version.ai_analysis" style="margin-left: 10px">
                    <el-tag :type="getRiskType(version.ai_analysis.risk_level)">
                      {{ getRiskText(version.ai_analysis.risk_level) }}
                    </el-tag>
                    <el-tag
                      :type="
                        getScoreType(version.ai_analysis.code_quality_score)
                      "
                      style="margin-left: 5px"
                    >
                      评分:
                      {{ version.ai_analysis.code_quality_score.toFixed(1) }}
                    </el-tag>
                  </span>
                </div>
                <div class="version-actions">
                  <el-button size="small" @click="handleViewCode(version)">
                    <el-icon><View /></el-icon>
                    查看代码包
                  </el-button>
                  <el-button
                    size="small"
                    type="success"
                    @click="showReviewDialog(version)"
                    v-if="canReview(version)"
                  >
                    <el-icon><Select /></el-icon>
                    审核
                  </el-button>
                  <el-button
                    size="small"
                    type="primary"
                    @click="handleDeploy(version)"
                    v-if="canDeploy(version)"
                  >
                    <el-icon><Position /></el-icon>
                    部署
                  </el-button>
                  <el-button
                    size="small"
                    type="warning"
                    @click="handleReanalyze(version)"
                    v-if="canReanalyze(version)"
                  >
                    <el-icon><RefreshRight /></el-icon>
                    重新分析
                  </el-button>
                  <el-button
                    size="small"
                    @click="showCompareDialog(version)"
                    v-if="version.version > 1"
                  >
                    <el-icon><Sort /></el-icon>
                    版本对比
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click="handleDeleteVersion(version)"
                    v-if="canDelete()"
                  >
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </div>
              </div>
            </template>

            <div class="version-content">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="上传者">{{
                  getUserName(version.uploaded_by)
                }}</el-descriptions-item>
                <el-descriptions-item label="上传时间">{{
                  formatDate(version.uploaded_at)
                }}</el-descriptions-item>
                <el-descriptions-item label="文件大小">{{
                  formatFileSize(version.file_size)
                }}</el-descriptions-item>
                <el-descriptions-item label="部署时间">{{
                  formatDate(version.deployed_at) || "-"
                }}</el-descriptions-item>
                <el-descriptions-item label="描述" :span="2">{{
                  version.description || "-"
                }}</el-descriptions-item>
              </el-descriptions>

              <!-- AI 分析结果 -->
              <div v-if="version.ai_analysis" class="ai-analysis">
                <el-divider>AI 分析结果</el-divider>
                <el-row :gutter="20">
                  <el-col :span="12">
                    <div class="analysis-item">
                      <span class="label">风险等级：</span>
                      <el-tag
                        :type="getRiskType(version.ai_analysis.risk_level)"
                      >
                        {{ getRiskText(version.ai_analysis.risk_level) }}
                      </el-tag>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div class="analysis-item">
                      <span class="label">代码质量评分：</span>
                      <el-tag
                        :type="
                          getScoreType(version.ai_analysis.code_quality_score)
                        "
                      >
                        {{ version.ai_analysis.code_quality_score.toFixed(1) }}
                      </el-tag>
                    </div>
                  </el-col>
                </el-row>

                <div
                  v-if="version.ai_analysis.security_issues?.length > 0"
                  class="issue-section"
                >
                  <h4>
                    🔴 安全问题 ({{
                      version.ai_analysis.security_issues.length
                    }})
                  </h4>
                  <el-collapse accordion style="margin-top: 10px">
                    <el-collapse-item
                      v-for="(issue, index) in version.ai_analysis
                        .security_issues"
                      :key="index"
                      :name="index"
                    >
                      <template #title>
                        <div class="issue-title-row">
                          <el-tag
                            :type="
                              issue.severity === 'critical'
                                ? 'danger'
                                : issue.severity === 'high'
                                ? 'danger'
                                : 'warning'
                            "
                            size="small"
                          >
                            {{
                              issue.severity === "critical"
                                ? "严重"
                                : issue.severity === "high"
                                ? "高危"
                                : issue.severity === "medium"
                                ? "中危"
                                : "低危"
                            }}
                          </el-tag>
                          <span class="file-path">{{ issue.file }}</span>
                          <span class="issue-desc">{{ issue.issue }}</span>
                        </div>
                      </template>
                      <div class="issue-detail">
                        <el-descriptions :column="1" border size="small">
                          <el-descriptions-item label="文件">{{
                            issue.file
                          }}</el-descriptions-item>
                          <el-descriptions-item label="行号">
                            <span v-if="issue.line_start && issue.line_end">
                              第 {{ issue.line_start }}-{{ issue.line_end }} 行
                            </span>
                            <span v-else>第 {{ issue.line }} 行</span>
                          </el-descriptions-item>
                          <el-descriptions-item label="严重程度">
                            <el-tag
                              :type="
                                issue.severity === 'critical'
                                  ? 'danger'
                                  : issue.severity === 'high'
                                  ? 'danger'
                                  : 'warning'
                              "
                            >
                              {{
                                issue.severity === "critical"
                                  ? "严重"
                                  : issue.severity === "high"
                                  ? "高"
                                  : issue.severity === "medium"
                                  ? "中"
                                  : "低"
                              }}
                            </el-tag>
                          </el-descriptions-item>
                        </el-descriptions>
                        <div v-if="issue.code_snippet" class="code-snippet">
                          <div class="snippet-label">问题代码：</div>
                          <pre><code>{{ issue.code_snippet }}</code></pre>
                        </div>
                        <div v-if="issue.suggestion" class="suggestion">
                          <div class="suggestion-label">💡 修复建议：</div>
                          <p>{{ issue.suggestion }}</p>
                        </div>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>

                <div
                  v-if="version.ai_analysis.performance_issues?.length > 0"
                  class="issue-section"
                >
                  <h4>
                    ⚠️ 性能问题 ({{
                      version.ai_analysis.performance_issues.length
                    }})
                  </h4>
                  <el-collapse accordion style="margin-top: 10px">
                    <el-collapse-item
                      v-for="(issue, index) in version.ai_analysis
                        .performance_issues"
                      :key="index"
                      :name="index"
                    >
                      <template #title>
                        <div class="issue-title-row">
                          <el-tag
                            :type="
                              issue.severity === 'high'
                                ? 'danger'
                                : issue.severity === 'medium'
                                ? 'warning'
                                : ''
                            "
                            size="small"
                          >
                            {{
                              issue.severity === "high"
                                ? "高危"
                                : issue.severity === "medium"
                                ? "中危"
                                : "低危"
                            }}
                          </el-tag>
                          <span class="file-path">{{ issue.file }}</span>
                          <span class="issue-desc">{{ issue.issue }}</span>
                        </div>
                      </template>
                      <div class="issue-detail">
                        <el-descriptions :column="1" border size="small">
                          <el-descriptions-item label="文件">{{
                            issue.file
                          }}</el-descriptions-item>
                          <el-descriptions-item label="行号">
                            <span v-if="issue.line_start && issue.line_end">
                              第 {{ issue.line_start }}-{{ issue.line_end }} 行
                            </span>
                            <span v-else>第 {{ issue.line }} 行</span>
                          </el-descriptions-item>
                          <el-descriptions-item label="严重程度">
                            <el-tag
                              :type="
                                issue.severity === 'high'
                                  ? 'danger'
                                  : issue.severity === 'medium'
                                  ? 'warning'
                                  : ''
                              "
                            >
                              {{
                                issue.severity === "high"
                                  ? "高"
                                  : issue.severity === "medium"
                                  ? "中"
                                  : "低"
                              }}
                            </el-tag>
                          </el-descriptions-item>
                        </el-descriptions>
                        <div v-if="issue.code_snippet" class="code-snippet">
                          <div class="snippet-label">问题代码：</div>
                          <pre><code>{{ issue.code_snippet }}</code></pre>
                        </div>
                        <div v-if="issue.suggestion" class="suggestion">
                          <div class="suggestion-label">💡 优化建议：</div>
                          <p>{{ issue.suggestion }}</p>
                        </div>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>

                <div
                  v-if="version.ai_analysis.code_smells?.length > 0"
                  class="issue-section"
                >
                  <h4>
                    📝 代码坏味道 ({{ version.ai_analysis.code_smells.length }})
                  </h4>
                  <el-collapse accordion style="margin-top: 10px">
                    <el-collapse-item
                      v-for="(issue, index) in version.ai_analysis.code_smells"
                      :key="index"
                      :name="index"
                    >
                      <template #title>
                        <div class="issue-title-row">
                          <el-tag type="info" size="small">低危</el-tag>
                          <span class="file-path">{{ issue.file }}</span>
                          <span class="issue-desc">{{ issue.issue }}</span>
                        </div>
                      </template>
                      <div class="issue-detail">
                        <el-descriptions :column="1" border size="small">
                          <el-descriptions-item label="文件">{{
                            issue.file
                          }}</el-descriptions-item>
                          <el-descriptions-item label="行号">
                            <span v-if="issue.line_start && issue.line_end">
                              第 {{ issue.line_start }}-{{ issue.line_end }} 行
                            </span>
                            <span v-else>第 {{ issue.line }} 行</span>
                          </el-descriptions-item>
                        </el-descriptions>
                        <div v-if="issue.code_snippet" class="code-snippet">
                          <div class="snippet-label">问题代码：</div>
                          <pre><code>{{ issue.code_snippet }}</code></pre>
                        </div>
                        <div v-if="issue.suggestion" class="suggestion">
                          <div class="suggestion-label">💡 重构建议：</div>
                          <p>{{ issue.suggestion }}</p>
                        </div>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>

                <div
                  v-if="version.ai_analysis.suggestions?.length > 0"
                  class="issue-section"
                >
                  <h4>改进建议</h4>
                  <ul>
                    <li
                      v-for="(suggestion, index) in version.ai_analysis
                        .suggestions"
                      :key="index"
                    >
                      {{ suggestion }}
                    </li>
                  </ul>
                </div>
              </div>

              <!-- 审核记录 -->
              <div v-if="version.review" class="review-section">
                <el-divider>审核记录</el-divider>
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="审核人">{{
                    version.review.reviewer_name
                  }}</el-descriptions-item>
                  <el-descriptions-item label="审核结果">
                    <el-tag
                      :type="
                        version.review.action === 'approved'
                          ? 'success'
                          : 'danger'
                      "
                    >
                      {{
                        version.review.action === "approved" ? "通过" : "拒绝"
                      }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="审核时间" :span="2">
                    {{ formatDate(version.review.reviewed_at) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="审核意见" :span="2">
                    {{ version.review.comment || "-" }}
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>

      <el-empty v-else description="暂无版本" />
    </el-card>

    <!-- 上传版本对话框 -->
    <el-dialog
      v-model="showUploadVersionDialog"
      title="上传新版本"
      width="600px"
    >
      <div class="upload-info">
        <p><strong>包名称：</strong>{{ deployment?.title }}</p>
        <p>
          <strong>当前版本：</strong>v{{ deployment?.current_version || 0 }}
        </p>
        <p>
          <strong>新版本号：</strong>v{{
            (deployment?.current_version || 0) + 1
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

    <!-- 审核对话框 -->
    <el-dialog v-model="showReviewDialogVisible" title="审核版本" width="600px">
      <el-form :model="reviewForm" ref="reviewFormRef" label-width="100px">
        <el-form-item label="版本">
          <el-tag type="info">v{{ selectedVersion?.version }}</el-tag>
        </el-form-item>
        <el-form-item label="审核结果" prop="action" required>
          <el-radio-group v-model="reviewForm.action">
            <el-radio label="approved">通过</el-radio>
            <el-radio label="rejected">拒绝</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="审核意见" prop="comment">
          <el-input
            v-model="reviewForm.comment"
            type="textarea"
            :rows="4"
            placeholder="请输入审核意见（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showReviewDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleReview" :loading="submitting"
          >提交</el-button
        >
      </template>
    </el-dialog>

    <!-- 版本对比对话框 -->
    <el-dialog
      v-model="showCompareDialogVisible"
      title="版本对比"
      width="800px"
    >
      <el-form :inline="true" label-width="90px">
        <el-form-item label="对比版本">
          <el-select
            v-model="compareVersion"
            placeholder="选择要对比的版本"
            style="width: 200px"
          >
            <el-option
              v-for="v in availableCompareVersions"
              :key="v.version"
              :label="`v${v.version}`"
              :value="v.version"
            />
          </el-select>
        </el-form-item>
        <el-form-item label-width="0">
          <el-button type="primary" @click="loadCompare">对比</el-button>
        </el-form-item>
      </el-form>

      <div v-if="compareData" class="compare-result">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="新增文件">{{
            compareData.summary.added
          }}</el-descriptions-item>
          <el-descriptions-item label="删除文件">{{
            compareData.summary.deleted
          }}</el-descriptions-item>
          <el-descriptions-item label="修改文件">{{
            compareData.summary.modified
          }}</el-descriptions-item>
          <el-descriptions-item label="总文件数">{{
            compareData.summary.total_files
          }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>文件变更详情</el-divider>

        <el-table
          :data="compareData.file_diffs"
          style="width: 100%"
          max-height="400"
        >
          <el-table-column prop="file" label="文件" min-width="200" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag
                :type="
                  row.status === 'added'
                    ? 'success'
                    : row.status === 'deleted'
                    ? 'danger'
                    : 'warning'
                "
              >
                {{
                  row.status === "added"
                    ? "新增"
                    : row.status === "deleted"
                    ? "删除"
                    : "修改"
                }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="说明" min-width="150" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                size="small"
                @click="showDiffDetail(row)"
                v-if="row.status === 'modified' && row.diff"
              >
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 代码查看对话框 -->
    <el-dialog
      v-model="showCodeViewerDialog"
      title="代码查看"
      width="80%"
      top="5vh"
    >
      <CodeViewer
        v-if="showCodeViewerDialog"
        :deployment-id="deployment?.id"
        :version="currentVersionForCode"
      />
    </el-dialog>

    <!-- 变更详情对话框 -->
    <el-dialog v-model="viewDiffDialogVisible" title="变更详情" width="800px">
      <div class="diff-viewer">
        <div class="diff-header">
          <span class="file-path">{{ currentDiff.file }}</span>
          <el-tag size="small">{{
            currentDiff.status === "modified"
              ? "修改"
              : currentDiff.status === "added"
              ? "新增"
              : "删除"
          }}</el-tag>
        </div>
        <div class="diff-content">
          <div
            v-for="(line, index) in getDiffLines(currentDiff.diff)"
            :key="index"
            :class="getDiffLineClass(line)"
            class="diff-line"
          >
            {{ line }}
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  ArrowLeft,
  Upload,
  Refresh,
  Select,
  Position,
  RefreshRight,
  Sort,
  Delete,
  View,
} from "@element-plus/icons-vue";
import CodeViewer from "@/components/CodeViewer.vue";
import { deploymentAPI, userAPI } from "@/api";
import { useUserStore } from "@/stores/user";

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const getDiffLines = (diff) => {
  if (!diff) return [];
  return diff.split("\n");
};

const getDiffLineClass = (line) => {
  if (line.startsWith("+") && !line.startsWith("+++")) return "diff-line-add";
  if (line.startsWith("-") && !line.startsWith("---"))
    return "diff-line-delete";
  if (line.startsWith("@@")) return "diff-line-info";
  return "diff-line-normal";
};

// 状态
const loading = ref(false);
const submitting = ref(false);
const deployment = ref(null);
const environmentName = ref("");
const users = ref([]); // 用户列表

// 对话框
const showUploadVersionDialog = ref(false);
const showReviewDialogVisible = ref(false);
const showCompareDialogVisible = ref(false);

// 表单
const uploadFormRef = ref();
const reviewFormRef = ref();
const uploadRef = ref();
const fileList = ref([]);
const selectedVersion = ref(null);
const compareVersion = ref(null);
const compareData = ref(null);

const uploadForm = ref({
  description: "",
  file: null,
});

const reviewForm = ref({
  action: "approved",
  comment: "",
});

// 计算属性
const sortedVersions = computed(() => {
  if (!deployment.value?.versions) return [];
  return [...deployment.value.versions].sort((a, b) => b.version - a.version);
});

const availableCompareVersions = computed(() => {
  if (!selectedVersion.value) return [];
  return sortedVersions.value.filter(
    (v) => v.version < selectedVersion.value.version
  );
});

// 权限判断
const canReview = (version) => {
  return (
    ["admin", "project_manager"].includes(userStore.user?.role) &&
    ["pending", "analysis_completed"].includes(version.status)
  );
};

const canDeploy = (version) => {
  return (
    ["admin", "project_manager"].includes(userStore.user?.role) &&
    version.status === "approved"
  );
};

const canReanalyze = (version) => {
  return ["admin", "project_manager"].includes(userStore.user?.role);
};

const canDelete = () => {
  return (
    userStore.user?.role === "admin" ||
    userStore.user?.role === "project_manager" ||
    deployment.value?.created_by === userStore.user?.id
  );
};

// 加载数据
const loadDeployment = async () => {
  loading.value = true;
  try {
    const response = await deploymentAPI.getDeployment(route.params.id);
    // 响应拦截器已经返回了 response.data，所以这里直接使用 response
    deployment.value = response;

    // 如果有环境配置，加载环境名称
    if (response.environment_id) {
      try {
        const { environmentAPI } = await import("@/api");
        const environments = await environmentAPI.getProjectEnvironments(
          response.project_id
        );
        const env = environments.find((e) => e.id === response.environment_id);
        if (env) {
          environmentName.value = env.name;
        }
      } catch (error) {
        console.error("加载环境名称失败", error);
      }
    }
  } catch (error) {
    ElMessage.error("加载发布详情失败");
  } finally {
    loading.value = false;
  }
};

// 上传版本
const showUploadDialog = () => {
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
    await deploymentAPI.uploadVersion(deployment.value.id, uploadForm.value);
    ElMessage.success("版本上传成功，AI分析中...");
    showUploadVersionDialog.value = false;
    loadDeployment();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "上传失败");
  } finally {
    submitting.value = false;
  }
};

// 审核
const showReviewDialog = (version) => {
  selectedVersion.value = version;
  reviewForm.value = {
    action: "approved",
    comment: "",
  };
  showReviewDialogVisible.value = true;
};

const handleReview = async () => {
  if (!reviewForm.value.action) {
    ElMessage.warning("请选择审核结果");
    return;
  }

  submitting.value = true;
  try {
    await deploymentAPI.reviewVersion(
      deployment.value.id,
      selectedVersion.value.version,
      reviewForm.value
    );
    ElMessage.success("审核完成");
    showReviewDialogVisible.value = false;
    loadDeployment();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "审核失败");
  } finally {
    submitting.value = false;
  }
};

// 部署
const handleDeploy = async (version) => {
  try {
    await ElMessageBox.confirm(
      `确定要部署版本 v${version.version} 吗？`,
      "确认部署",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }
    );

    await deploymentAPI.deployVersion(deployment.value.id, version.version);
    ElMessage.success("部署成功");
    loadDeployment();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error(error.response?.data?.detail || "部署失败");
    }
  }
};

// 重新分析
const handleReanalyze = async (version) => {
  try {
    await deploymentAPI.reanalyzeVersion(deployment.value.id, version.version);
    ElMessage.success("已启动AI重新分析，请稍后刷新查看结果");
    setTimeout(() => loadDeployment(), 2000);
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "重新分析失败");
  }
};

// 删除版本
const handleDeleteVersion = async (version) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除版本 v${version.version} 吗？`,
      "确认删除",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }
    );

    await deploymentAPI.deleteVersion(deployment.value.id, version.version);
    ElMessage.success("删除成功");
    loadDeployment();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
};

// 代码查看
const showCodeViewerDialog = ref(false);
const currentVersionForCode = ref(0);
const handleViewCode = (version) => {
  currentVersionForCode.value = version.version;
  showCodeViewerDialog.value = true;
};

// 变更详情
const viewDiffDialogVisible = ref(false);
const currentDiff = ref({});
const showDiffDetail = (row) => {
  if (row.diff) {
    currentDiff.value = row;
    viewDiffDialogVisible.value = true;
  } else {
    ElMessage.info("暂无变更详情");
  }
};

// 版本对比
const showCompareDialog = (version) => {
  selectedVersion.value = version;
  compareVersion.value = version.version - 1;
  compareData.value = null;
  showCompareDialogVisible.value = true;
};

const loadCompare = async () => {
  if (!compareVersion.value) {
    ElMessage.warning("请选择要对比的版本");
    return;
  }

  try {
    const response = await deploymentAPI.compareVersions(
      deployment.value.id,
      selectedVersion.value.version,
      compareVersion.value
    );
    // 响应拦截器已经返回了 response.data，所以这里直接使用 response
    compareData.value = response;
  } catch (error) {
    ElMessage.error("版本对比失败");
  }
};

// 工具函数
const getUserName = (userId) => {
  const user = users.value.find((u) => u.id === userId);
  return user ? user.full_name : userId;
};

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

const getRiskType = (risk) => {
  const riskMap = {
    low: "success",
    medium: "warning",
    high: "danger",
    critical: "danger",
  };
  return riskMap[risk] || "info";
};

const getRiskText = (risk) => {
  const riskMap = {
    low: "低风险",
    medium: "中风险",
    high: "高风险",
    critical: "严重风险",
  };
  return riskMap[risk] || risk;
};

const getScoreType = (score) => {
  if (score >= 80) return "success";
  if (score >= 60) return "warning";
  return "danger";
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

const formatFileSize = (bytes) => {
  if (!bytes) return "-";
  const units = ["B", "KB", "MB", "GB"];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`;
};

// 加载用户列表
const loadUsers = async () => {
  try {
    users.value = await userAPI.getUsers();
  } catch (error) {
    console.error("加载用户列表失败", error);
  }
};

// 初始化
onMounted(() => {
  loadDeployment();
  loadUsers();
});
</script>

<style scoped>
.deployment-detail-page {
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
  gap: 10px;
}

.header-left h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.info-card {
  margin-bottom: 20px;
}

.versions-card {
  margin-bottom: 20px;
}

.version-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.version-title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.version-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.version-content {
  padding: 10px 0;
}

.ai-analysis {
  margin-top: 20px;
}

.analysis-item {
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.analysis-item .label {
  font-weight: 500;
  margin-right: 10px;
}

.issue-section {
  margin-top: 20px;
}

.issue-section h4 {
  margin-bottom: 10px;
  color: #303133;
  font-weight: 600;
  font-size: 16px;
  padding: 10px 0;
  border-bottom: 2px solid #f0f0f0;
}

.issue-section ul {
  padding-left: 20px;
}

.issue-section li {
  margin-bottom: 5px;
}

.issue-title {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
}

.issue-title-row {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-path {
  font-family: "Consolas", "Monaco", "Courier New", monospace;
  font-size: 13px;
  color: #0969da;
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
}

.issue-desc {
  font-size: 14px;
  color: #24292f;
  line-height: 1.5;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.issue-detail {
  padding: 10px 0;
}

.code-snippet {
  margin-top: 15px;
  background: #f6f8fa;
  border-radius: 6px;
  padding: 12px;
  border-left: 3px solid #0969da;
}

.snippet-label {
  font-weight: 600;
  color: #24292f;
  margin-bottom: 8px;
  font-size: 13px;
}

.code-snippet pre {
  margin: 0;
  padding: 0;
  background: transparent;
  overflow-x: auto;
}

.code-snippet code {
  font-family: "Consolas", "Monaco", "Courier New", monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #24292f;
  white-space: pre;
}

.suggestion {
  margin-top: 15px;
  background: #f0f9ff;
  border-radius: 6px;
  padding: 12px;
  border-left: 3px solid #0284c7;
}

.suggestion-label {
  font-weight: 600;
  color: #0c4a6e;
  margin-bottom: 8px;
  font-size: 13px;
}

.suggestion p {
  margin: 0;
  color: #1e3a8a;
  line-height: 1.6;
  font-size: 14px;
}

.review-section {
  margin-top: 20px;
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

.compare-result {
  margin-top: 20px;
}

.diff-viewer {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.diff-header {
  padding: 10px 15px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.diff-content {
  padding: 0;
  max-height: 500px;
  overflow: auto;
  background-color: white;
}

.diff-content pre {
  margin: 0;
  padding: 15px;
  font-family: Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre;
}

.diff-line {
  padding: 0 10px;
  min-height: 20px;
  line-height: 20px;
  font-family: Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}

.diff-line-add {
  background-color: #e6ffec;
  color: #1f883d;
}

.diff-line-delete {
  background-color: #ffebe9;
  color: #cf222e;
}

.diff-line-info {
  color: #8250df;
  background-color: #f6f8fa;
  font-weight: bold;
}
</style>
