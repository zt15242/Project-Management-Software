<template>
  <div class="topic-detail-page">
    <el-button :icon="ArrowLeft" @click="goBack" class="back-button"
      >返回</el-button
    >

    <div v-if="loading" class="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <div v-else-if="topic" class="content">
      <!-- topic基本信息 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <h2 v-if="!isEditing">{{ topic.title }}</h2>
            <el-input
              v-else
              v-model="editForm.title"
              placeholder="请输入课题标题"
              size="large"
              style="max-width: 600px"
            />
            <div class="header-actions">
              <el-tag
                :type="
                  getStatusType(isEditing ? editForm.status : topic.status)
                "
                size="large"
              >
                {{ getStatusLabel(isEditing ? editForm.status : topic.status) }}
              </el-tag>
              <el-tag
                :type="
                  getSeverityType(
                    isEditing ? editForm.severity : topic.severity
                  )
                "
                size="large"
                style="margin-left: 10px"
              >
                {{
                  getSeverityLabel(
                    isEditing ? editForm.severity : topic.severity
                  )
                }}
              </el-tag>
            </div>
          </div>
        </template>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="项目名称">{{
            getProjectName(topic.project_id)
          }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag
              v-if="!isEditing || !isAdmin"
              :type="getStatusType(topic.status)"
            >
              {{ getStatusLabel(topic.status) }}
            </el-tag>
            <el-select
              v-else
              v-model="editForm.status"
              size="small"
              style="width: 100%"
            >
              <el-option label="打开" value="open" />
              <el-option label="已分配" value="assigned" />
              <el-option label="处理中" value="in_progress" />
              <el-option label="已修复" value="fixed" />
              <el-option label="测试中" value="testing" />
              <el-option label="已关闭" value="closed" />
              <el-option label="重新打开" value="reopened" />
            </el-select>
            <span
              v-if="isEditing && !isAdmin"
              style="color: #909399; font-size: 12px; margin-left: 8px"
            >
              (仅管理员可修改)
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="创建人">{{
            getUserName(topic.created_by)
          }}</el-descriptions-item>
          <el-descriptions-item label="负责人">
            <span v-if="!isEditing">{{
              getUserName(topic.assigned_to) || "未分配"
            }}</span>
            <el-select
              v-else
              v-model="editForm.assigned_to"
              clearable
              size="small"
              style="width: 100%"
            >
              <el-option
                v-for="user in users"
                :key="user.id"
                :label="user.full_name"
                :value="user.id"
              />
            </el-select>
          </el-descriptions-item>
          <el-descriptions-item label="严重程度">
            <el-tag v-if="!isEditing" :type="getSeverityType(topic.severity)">
              {{ getSeverityLabel(topic.severity) }}
            </el-tag>
            <el-select
              v-else
              v-model="editForm.severity"
              size="small"
              style="width: 100%"
            >
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="严重" value="critical" />
            </el-select>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{
            formatDateTime(topic.created_at)
          }}</el-descriptions-item>
          <el-descriptions-item label="更新时间" :span="2">{{
            formatDateTime(topic.updated_at)
          }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            <div v-if="!isEditing" class="description">
              {{ topic.description }}
            </div>
            <el-input
              v-else
              v-model="editForm.description"
              type="textarea"
              :rows="3"
            />
          </el-descriptions-item>
          <el-descriptions-item label="复现步骤" :span="2">
            <div v-if="!isEditing" class="steps">
              {{ topic.steps_to_reproduce || "无" }}
            </div>
            <el-input
              v-else
              v-model="editForm.steps_to_reproduce"
              type="textarea"
              :rows="3"
              placeholder="请输入复现步骤"
            />
          </el-descriptions-item>
          <el-descriptions-item label="修复说明" :span="2">
            <div v-if="!isEditing" class="fix-desc">
              {{ topic.fix_description || "无" }}
            </div>
            <el-input
              v-else
              v-model="editForm.fix_description"
              type="textarea"
              :rows="3"
              placeholder="请输入修复说明"
            />
          </el-descriptions-item>
        </el-descriptions>

        <!-- 操作按钮 -->
        <div class="actions">
          <!-- 编辑模式下的按钮 -->
          <template v-if="isEditing">
            <el-button type="primary" :loading="submitting" @click="handleSave">
              <el-icon><Check /></el-icon>
              保存
            </el-button>
            <el-button @click="handleCancelEdit">
              <el-icon><Close /></el-icon>
              取消
            </el-button>
          </template>

          <!-- 查看模式下的按钮 -->
          <template v-else>
            <!-- 接收topic：被分配人可以接收处理 -->
            <el-button
              v-if="canAccept"
              type="success"
              @click="handleAccepttopic"
            >
              接收topic
            </el-button>

            <!-- 流转topic：负责人可以转给其他人 -->
            <el-button
              v-if="canTransfer"
              type="warning"
              @click="handleTransfertopic"
            >
              流转
            </el-button>

            <!-- 修复提测（提交复测）：处理中的topic修复完成后提交给创建者复测 -->
            <el-button
              v-if="canSubmitRetest"
              type="success"
              @click="handleSubmitRetest"
            >
              修复提测
            </el-button>

            <!-- 复测操作：创建者进行复测 -->
            <el-dropdown v-if="canRetest" @command="handleRetestAction">
              <el-button type="warning" :icon="ArrowDown"> 复测操作 </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="pass">复测通过</el-dropdown-item>
                  <el-dropdown-item command="fail">复测失败</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>

            <!-- 编辑topic -->
            <el-button
              v-if="canEdit"
              type="primary"
              :icon="Edit"
              @click="handleEdit"
            >
              编辑
            </el-button>

            <!-- 删除topic -->
            <el-button
              v-if="canDelete"
              type="danger"
              :icon="Delete"
              @click="handleDelete"
            >
              删除
            </el-button>
          </template>
        </div>
      </el-card>

      <!-- 课题截图 -->
      <el-card
        class="images-card"
        v-if="validtopicImages.length > 0 || (isEditing && canEdittopicImages)"
      >
        <template #header>
          <div
            style="
              display: flex;
              justify-content: space-between;
              align-items: center;
            "
          >
            <h3>课题截图</h3>
            <el-upload
              v-if="isEditing && canEdittopicImages"
              :auto-upload="false"
              :on-change="handletopicImageChange"
              :file-list="topicImageFileList"
              :show-file-list="false"
              accept="image/*"
              multiple
            >
              <el-button size="small" type="primary" :icon="Plus"
                >添加图片</el-button
              >
            </el-upload>
            <span
              v-else-if="isEditing && !canEdittopicImages"
              style="color: #909399; font-size: 12px"
            >
              (仅创建者和管理员可修改)
            </span>
          </div>
        </template>
        <div class="image-gallery">
          <div
            v-for="(image, index) in isEditing && canEdittopicImages
              ? topicImageFileList
              : validtopicImages"
            :key="`topic-img-${index}`"
            class="image-wrapper"
          >
            <el-image
              v-if="!isEditing || !canEdittopicImages"
              :src="image"
              :preview-src-list="validtopicImages"
              :initial-index="index"
              fit="cover"
              class="topic-image"
              :preview-teleported="true"
              lazy
            >
              <template #error>
                <div class="image-error">
                  <el-icon><Picture /></el-icon>
                  <span>图片加载失败</span>
                </div>
              </template>
            </el-image>
            <div v-else class="edit-image-wrapper">
              <el-image
                :src="image.url || image"
                fit="cover"
                class="topic-image"
              />
              <div class="image-overlay">
                <el-button
                  size="small"
                  type="danger"
                  circle
                  :icon="Delete"
                  @click="removetopicImage(index)"
                />
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 修复截图 -->
      <el-card
        class="images-card"
        v-if="validFixImages.length > 0 || (isEditing && canEditFixImages)"
      >
        <template #header>
          <div
            style="
              display: flex;
              justify-content: space-between;
              align-items: center;
            "
          >
            <h3>修复截图</h3>
            <el-upload
              v-if="isEditing && canEditFixImages"
              :auto-upload="false"
              :on-change="handleFixImageChange"
              :file-list="fixImageFileList"
              :show-file-list="false"
              accept="image/*"
              multiple
            >
              <el-button size="small" type="primary" :icon="Plus"
                >添加图片</el-button
              >
            </el-upload>
          </div>
        </template>
        <div class="image-gallery">
          <div
            v-for="(image, index) in isEditing && canEditFixImages
              ? fixImageFileList
              : validFixImages"
            :key="`fix-img-${index}`"
            class="image-wrapper"
          >
            <el-image
              v-if="!isEditing || !canEditFixImages"
              :src="image"
              :preview-src-list="validFixImages"
              :initial-index="index"
              fit="cover"
              class="topic-image"
              :preview-teleported="true"
              lazy
            >
              <template #error>
                <div class="image-error">
                  <el-icon><Picture /></el-icon>
                  <span>图片加载失败</span>
                </div>
              </template>
            </el-image>
            <div v-else class="edit-image-wrapper">
              <el-image
                :src="image.url || image"
                fit="cover"
                class="topic-image"
              />
              <div class="image-overlay">
                <el-button
                  size="small"
                  type="danger"
                  circle
                  :icon="Delete"
                  @click="removeFixImage(index)"
                />
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 流转topic对话框 -->
      <el-dialog
        v-model="transferDialogVisible"
        title="流转topic"
        width="500px"
        :close-on-click-modal="false"
      >
        <el-form label-width="100px">
          <el-form-item label="当前负责人">
            <span>{{ getUserName(topic.assigned_to) || "未分配" }}</span>
          </el-form-item>
          <el-form-item label="流转给" required>
            <el-select
              v-model="transferToUserId"
              placeholder="请选择开发人员"
              style="width: 100%"
            >
              <el-option
                v-for="user in users"
                :key="user.id"
                :label="user.full_name"
                :value="user.id"
                :disabled="user.id === topic.assigned_to"
              />
            </el-select>
          </el-form-item>
          <el-alert
            title="流转后课题状态将变为'已分配'，需要新负责人接收后才能开始处理"
            type="info"
            :closable="false"
            show-icon
            style="margin-top: 10px"
          />
        </el-form>
        <template #footer>
          <el-button @click="transferDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmTransfer"
            >确认流转</el-button
          >
        </template>
      </el-dialog>

      <!-- 评论区域 -->
      <el-card class="comments-card">
        <template #header>
          <h3>讨论交流</h3>
        </template>

        <!-- 评论输入框 -->
        <div class="comment-input">
          <el-input
            v-model="commentContent"
            type="textarea"
            :rows="3"
            placeholder="输入评论内容..."
            maxlength="500"
            show-word-limit
          />
          <el-button
            type="primary"
            @click="handleAddComment"
            :disabled="!commentContent.trim()"
            style="margin-top: 10px"
          >
            发表评论
          </el-button>
        </div>

        <!-- 评论列表 -->
        <div class="comments-list">
          <el-empty v-if="comments.length === 0" description="暂无评论" />
          <div
            v-for="comment in comments"
            :key="comment.id"
            class="comment-item"
          >
            <div class="comment-header">
              <span class="comment-user">{{ comment.user_name }}</span>
              <span class="comment-time">{{
                formatDateTime(comment.created_at)
              }}</span>
            </div>
            <div class="comment-content">{{ comment.content }}</div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { topicAPI, projectAPI, userAPI } from "@/api";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  ArrowLeft,
  Edit,
  Delete,
  ArrowDown,
  Plus,
  Loading,
  Picture,
  Check,
  Close,
} from "@element-plus/icons-vue";
import { useUserStore } from "@/stores/user";
import { useNotificationStore } from "@/stores/notification";
import dayjs from "dayjs";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const notificationStore = useNotificationStore();

const topic = ref(null);
const projects = ref([]);
const users = ref([]);
const loading = ref(true);
const submitting = ref(false);
const isEditing = ref(false);

// 评论相关
const comments = ref([]);
const commentContent = ref("");

// 图片上传相关
const topicImageFileList = ref([]);
const fixImageFileList = ref([]);

// 编辑表单
const editForm = reactive({
  title: "",
  description: "",
  steps_to_reproduce: "",
  assigned_to: "",
  severity: "medium",
  status: "open",
  fix_description: "",
});

// 当前用户信息
const currentUserId = computed(() => userStore.userId);
const isAdmin = computed(() => userStore.isAdmin);
const isCreator = computed(
  () => topic.value && topic.value.created_by === currentUserId.value
);
const isAssignee = computed(
  () => topic.value && topic.value.assigned_to === currentUserId.value
);

// 获取有效的图片列表
const validtopicImages = computed(() => {
  if (!topic.value || !topic.value.topic_images) return [];
  return topic.value.topic_images.filter((img) => img && img.length > 0);
});

const validFixImages = computed(() => {
  if (!topic.value || !topic.value.fix_images) return [];
  return topic.value.fix_images.filter((img) => img && img.length > 0);
});

// 权限控制
const canEdit = computed(() => {
  if (!topic.value) return false;
  return isAdmin.value || isCreator.value || isAssignee.value;
});

// 课题截图编辑权限：仅创建者和管理员
const canEdittopicImages = computed(() => {
  if (!topic.value) return false;
  return isAdmin.value || isCreator.value;
});

// 修复截图编辑权限：负责人、创建者和管理员
const canEditFixImages = computed(() => {
  if (!topic.value) return false;
  return isAdmin.value || isCreator.value || isAssignee.value;
});

// 可以接收topic：状态为已分配(assigned)且是负责人
const canAccept = computed(() => {
  if (!topic.value) return false;
  return (
    topic.value.assigned_to === currentUserId.value &&
    topic.value.status === "assigned"
  );
});

// 可以流转topic：负责人可以流转（除了已关闭的）
const canTransfer = computed(() => {
  if (!topic.value) return false;
  return (
    (topic.value.assigned_to === currentUserId.value || isAdmin.value) &&
    topic.value.status !== "closed"
  );
});

// 可以提交复测：状态为处理中(in_progress)且是负责人
const canSubmitRetest = computed(() => {
  if (!topic.value) return false;
  return (
    topic.value.assigned_to === currentUserId.value &&
    topic.value.status === "in_progress"
  );
});

// 可以进行复测：状态为测试中(testing)且是创建者
const canRetest = computed(() => {
  if (!topic.value) return false;
  return (
    topic.value.created_by === currentUserId.value &&
    topic.value.status === "testing"
  );
});

const canDelete = computed(() => {
  if (!topic.value) return false;
  return isAdmin.value || topic.value.created_by === currentUserId.value;
});

const goBack = () => {
  router.back();
};

// 验证和修复图片URL
const fixImageUrl = (img) => {
  try {
    // 检查是否为空或无效
    if (!img || typeof img !== "string" || img.trim() === "") {
      return null;
    }

    const trimmedImg = img.trim();

    // 如果已经是完整的data URL，直接返回
    if (trimmedImg.startsWith("data:image/")) {
      return trimmedImg;
    }

    // 检查是否看起来像base64数据
    // Base64字符串应该只包含 A-Z, a-z, 0-9, +, /, = 字符
    if (trimmedImg.length > 100) {
      // 检测图片类型
      let mimeType = "image/png"; // 默认

      if (trimmedImg.startsWith("/9j/")) {
        mimeType = "image/jpeg";
      } else if (trimmedImg.startsWith("iVBORw0KGgo")) {
        mimeType = "image/png";
      } else if (trimmedImg.startsWith("R0lGOD")) {
        mimeType = "image/gif";
      } else if (trimmedImg.startsWith("UklGR")) {
        mimeType = "image/webp";
      }

      // 验证是否为有效的base64
      const base64Regex = /^[A-Za-z0-9+/]+=*$/;
      if (base64Regex.test(trimmedImg.substring(0, 100))) {
        return `data:${mimeType};base64,${trimmedImg}`;
      }
    }

    // 如果都不是，可能是相对路径或URL
    if (
      trimmedImg.startsWith("http://") ||
      trimmedImg.startsWith("https://") ||
      trimmedImg.startsWith("/")
    ) {
      return trimmedImg;
    }

    console.warn("无法识别的图片格式:", trimmedImg.substring(0, 50));
    return null;
  } catch (error) {
    console.error("处理图片URL时出错:", error);
    return null;
  }
};

const fetchTopicDetail = async () => {
  loading.value = true;
  try {
    const topicData = await topicAPI.getTopic(route.params.id);

    // 调试输出
    console.log("原始topic数据:", {
      topic_images: topicData.topic_images,
      fix_images: topicData.fix_images,
    });

    // 确保图片数据有正确的格式（一次性处理，避免重复渲染）
    if (topicData.topic_images && Array.isArray(topicData.topic_images)) {
      topicData.topic_images = topicData.topic_images
        .map(fixImageUrl)
        .filter((img) => img !== null && img.length > 0);

      console.log(
        "处理后的课题截图:",
        topicData.topic_images.map((img) => img.substring(0, 50))
      );
    } else {
      topicData.topic_images = [];
    }

    if (topicData.fix_images && Array.isArray(topicData.fix_images)) {
      topicData.fix_images = topicData.fix_images
        .map(fixImageUrl)
        .filter((img) => img !== null && img.length > 0);

      console.log(
        "处理后的修复截图:",
        topicData.fix_images.map((img) => img.substring(0, 50))
      );
    } else {
      topicData.fix_images = [];
    }

    // 一次性赋值，避免多次触发响应式更新
    topic.value = topicData;

    await fetchComments(route.params.id);
  } catch (error) {
    console.error("Failed to fetch topic detail:", error);
    ElMessage.error("获取课题详情失败");
    goBack();
  } finally {
    loading.value = false;
  }
};

const fetchProjects = async () => {
  try {
    const data = await projectAPI.getProjects({ limit: 100 });
    projects.value = data.items || [];
  } catch (error) {
    console.error("获取项目列表失败:", error);
  }
};

const fetchUsers = async () => {
  try {
    users.value = await userAPI.getUsers();
  } catch (error) {
    console.error("获取用户列表失败:", error);
  }
};

const fetchComments = async (topicId) => {
  try {
    comments.value = await topicAPI.getComments(topicId);
  } catch (error) {
    console.error("获取评论失败:", error);
  }
};

const handleAddComment = async () => {
  if (!commentContent.value.trim()) {
    return;
  }

  try {
    await topicAPI.addComment(topic.value.id, {
      content: commentContent.value.trim(),
    });
    ElMessage.success("评论发表成功");
    commentContent.value = "";
    await fetchComments(topic.value.id);
    notificationStore.fetchUnreadCount();
  } catch (error) {
    ElMessage.error("发表评论失败");
  }
};

// 图片转base64
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = (error) => reject(error);
  });
};

const handletopicImageChange = async (file, fileList) => {
  topicImageFileList.value = fileList;
};

const handleFixImageChange = async (file, fileList) => {
  fixImageFileList.value = fileList;
};

const handleEdit = () => {
  // 进入编辑模式
  isEditing.value = true;

  // 复制当前数据到编辑表单
  Object.assign(editForm, {
    title: topic.value.title,
    description: topic.value.description,
    steps_to_reproduce: topic.value.steps_to_reproduce || "",
    assigned_to: topic.value.assigned_to,
    severity: topic.value.severity,
    status: topic.value.status,
    fix_description: topic.value.fix_description || "",
  });

  // 只有有权限才显示对应的已有图片用于编辑
  if (canEdittopicImages.value) {
    topicImageFileList.value = topic.value.topic_images
      ? topic.value.topic_images.map((img, index) => ({
          name: `topic_image_${index}`,
          url: img,
          uid: -1 - index,
        }))
      : [];
  } else {
    topicImageFileList.value = [];
  }

  if (canEditFixImages.value) {
    fixImageFileList.value = topic.value.fix_images
      ? topic.value.fix_images.map((img, index) => ({
          name: `fix_image_${index}`,
          url: img,
          uid: -1000 - index,
        }))
      : [];
  } else {
    fixImageFileList.value = [];
  }
};

const handleCancelEdit = () => {
  ElMessageBox.confirm("确定要取消编辑吗？未保存的更改将丢失。", "取消编辑", {
    confirmButtonText: "确定",
    cancelButtonText: "继续编辑",
    type: "warning",
  })
    .then(() => {
      isEditing.value = false;
      topicImageFileList.value = [];
      fixImageFileList.value = [];
    })
    .catch(() => {
      // 用户选择继续编辑，不做任何操作
    });
};

// 删除topic图片
const removetopicImage = (index) => {
  topicImageFileList.value.splice(index, 1);
  ElMessage.success("图片已移除");
};

// 删除修复图片
const removeFixImage = (index) => {
  fixImageFileList.value.splice(index, 1);
  ElMessage.success("图片已移除");
};

const handleSave = async () => {
  // 简单验证
  if (!editForm.title || !editForm.title.trim()) {
    ElMessage.warning("请输入课题标题");
    return;
  }

  if (!editForm.description || !editForm.description.trim()) {
    ElMessage.warning("请输入课题描述");
    return;
  }

  submitting.value = true;
  try {
    const updateData = { ...editForm };

    // 只有有权限才处理课题截图
    if (canEdittopicImages.value) {
      const topicImages = [];
      for (const file of topicImageFileList.value) {
        if (file.raw) {
          const base64 = await fileToBase64(file.raw);
          topicImages.push(base64);
        } else if (file.url) {
          // 保持已有图片的原始格式
          topicImages.push(file.url);
        }
      }
      updateData.topic_images = topicImages.filter(
        (img) => img && img.length > 0
      );
    } else {
      // 无权限则保持原有的课题截图
      updateData.topic_images = topic.value.topic_images || [];
    }

    // 只有有权限才处理修复截图
    if (canEditFixImages.value) {
      const fixImages = [];
      for (const file of fixImageFileList.value) {
        if (file.raw) {
          const base64 = await fileToBase64(file.raw);
          fixImages.push(base64);
        } else if (file.url) {
          fixImages.push(file.url);
        }
      }
      updateData.fix_images = fixImages.filter((img) => img && img.length > 0);
    } else {
      // 无权限则保持原有的修复截图
      updateData.fix_images = topic.value.fix_images || [];
    }

    console.log("提交的更新数据:", {
      title: updateData.title,
      status: updateData.status,
      topic_images_count: updateData.topic_images.length,
      fix_images_count: updateData.fix_images.length,
      canEdittopicImages: canEdittopicImages.value,
      canEditFixImages: canEditFixImages.value,
    });

    await topicAPI.updateTopic(topic.value.id, updateData);
    ElMessage.success("topic更新成功");

    // 退出编辑模式
    isEditing.value = false;
    topicImageFileList.value = [];
    fixImageFileList.value = [];

    // 重新加载详情，确保显示最新数据
    await fetchTopicDetail();
    notificationStore.fetchUnreadCount();
  } catch (error) {
    console.error("更新topic失败:", error);
    ElMessage.error(
      "操作失败: " + (error.response?.data?.detail || error.message)
    );
  } finally {
    submitting.value = false;
  }
};

// 接收topic - 将状态从assigned改为in_progress
const handleAccepttopic = async () => {
  try {
    await ElMessageBox.confirm("确认接收此topic并开始处理？", "接收topic", {
      type: "info",
      confirmButtonText: "确认接收",
      cancelButtonText: "取消",
    });

    await topicAPI.updateTopic(topic.value.id, { status: "in_progress" });
    ElMessage.success("已接收topic，开始处理");
    await fetchTopicDetail();
    notificationStore.fetchUnreadCount();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("接收失败");
    }
  }
};

// 流转topic - 转给其他开发人员
const transferDialogVisible = ref(false);
const transferToUserId = ref("");

const handleTransfertopic = () => {
  transferToUserId.value = topic.value.assigned_to || "";
  transferDialogVisible.value = true;
};

const confirmTransfer = async () => {
  if (!transferToUserId.value) {
    ElMessage.warning("请选择要流转的开发人员");
    return;
  }

  if (transferToUserId.value === topic.value.assigned_to) {
    ElMessage.warning("请选择不同的开发人员");
    return;
  }

  try {
    await topicAPI.updateTopic(topic.value.id, {
      assigned_to: transferToUserId.value,
      status: "assigned", // 流转后状态改为已分配
    });

    ElMessage.success("topic已流转");
    transferDialogVisible.value = false;
    await fetchTopicDetail();
    notificationStore.fetchUnreadCount();
  } catch (error) {
    ElMessage.error("流转失败");
  }
};

// 修复提测（提交复测）- 将状态从in_progress直接改为testing
const handleSubmitRetest = async () => {
  try {
    await ElMessageBox.confirm(
      "确认课题已修复并提交复测？提交后将通知创建者进行验证。",
      "修复提测",
      {
        type: "success",
        confirmButtonText: "确认提交",
        cancelButtonText: "取消",
      }
    );
    await topicAPI.startRetest(topic.value.id);
    ElMessage.success("已提交复测，等待创建者验证");
    await fetchTopicDetail();
    notificationStore.fetchUnreadCount();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("提交失败");
    }
  }
};

const handleRetestAction = async (command) => {
  try {
    if (command === "pass") {
      await ElMessageBox.confirm(
        "确认课题已修复，通过复测并关闭？",
        "复测通过",
        {
          type: "success",
          confirmButtonText: "确认通过",
          cancelButtonText: "取消",
        }
      );
      await topicAPI.closeTopic(topic.value.id);
      ElMessage.success("复测通过，课题已关闭");
    } else if (command === "fail") {
      await ElMessageBox.confirm(
        '确认课题未修复，打回重新处理？topic将退回至"已分配"状态，负责人需重新接收。',
        "复测失败",
        {
          type: "warning",
          confirmButtonText: "确认打回",
          cancelButtonText: "取消",
        }
      );
      await topicAPI.reopenTopic(topic.value.id);
      ElMessage.warning('课题已打回至"已分配"状态，负责人需重新接收处理');
    }
    await fetchTopicDetail();
    notificationStore.fetchUnreadCount();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("操作失败");
    }
  }
};

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      "确认删除此topic？此操作不可撤销。",
      "删除确认",
      { type: "warning" }
    );
    await topicAPI.deleteTopic(topic.value.id);
    ElMessage.success("删除成功");
    goBack();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
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

const getStatusType = (status) => {
  const types = {
    open: "info",
    assigned: "warning",
    in_progress: "warning",
    fixed: "success",
    testing: "warning",
    closed: "success",
    reopened: "danger",
  };
  return types[status] || "info";
};

const getStatusLabel = (status) => {
  const labels = {
    open: "打开",
    assigned: "已分配",
    in_progress: "处理中",
    fixed: "已修复",
    testing: "测试中",
    closed: "已关闭",
    reopened: "重新打开",
  };
  return labels[status] || status;
};

const getSeverityType = (severity) => {
  const types = {
    low: "info",
    medium: "",
    high: "warning",
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

const formatDateTime = (date) => {
  return dayjs(date).format("YYYY-MM-DD HH:mm:ss");
};

onMounted(() => {
  fetchTopicDetail();
  fetchProjects();
  fetchUsers();
});
</script>

<style scoped>
.topic-detail-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.back-button {
  margin-bottom: 20px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 0;
  font-size: 16px;
  color: #999;
}

.loading .el-icon {
  font-size: 40px;
  margin-bottom: 10px;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-card .card-header h2 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.description,
.steps,
.fix-desc {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.images-card h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.image-gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.image-wrapper {
  width: 150px;
  height: 150px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #ddd;
}

.topic-image {
  width: 100%;
  height: 100%;
  cursor: pointer;
  transition: all 0.3s;
  object-fit: cover;
}

.topic-image:hover {
  transform: scale(1.05);
}

.image-wrapper:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 防止图片加载时闪烁 */
.topic-image :deep(img) {
  background-color: #f5f7fa;
  image-rendering: -webkit-optimize-contrast;
  image-rendering: crisp-edges;
}

/* 优化预览体验 */
.el-image-viewer__wrapper {
  z-index: 9999 !important;
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background-color: #f5f7fa;
  color: #909399;
  font-size: 12px;
}

.image-error .el-icon {
  font-size: 30px;
  margin-bottom: 8px;
}

/* 编辑模式下的图片 */
.edit-image-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.edit-image-wrapper:hover .image-overlay {
  opacity: 1;
}

.comments-card h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.comment-input {
  margin-bottom: 25px;
}

.comments-list {
  max-height: 500px;
  overflow-y: auto;
}

.comment-item {
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 12px;
  transition: all 0.3s;
}

.comment-item:hover {
  background: #f0f2f5;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.comment-user {
  font-weight: 600;
  color: #409eff;
  font-size: 14px;
}

.comment-time {
  font-size: 12px;
  color: #999;
}

.comment-content {
  color: #333;
  line-height: 1.6;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>

