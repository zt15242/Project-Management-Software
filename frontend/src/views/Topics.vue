<template>
  <div class="topics">
    <div class="page-header">
      <h1>课题管理</h1>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog"
        >创建课题</el-button
      >
    </div>

    <el-card>
      <div class="filter-bar">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索课题号/标题/描述"
          clearable
          @clear="fetchTopics"
          @keyup.enter="fetchTopics"
          style="width: 250px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select
          v-model="filters.project_id"
          placeholder="选择项目"
          clearable
          @change="fetchTopics"
          style="width: 200px"
        >
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>
        <el-select
          v-model="filters.status"
          placeholder="课题状态"
          clearable
          @change="fetchTopics"
          style="width: 150px"
        >
          <el-option label="打开" value="open" />
          <el-option label="已分配" value="assigned" />
          <el-option label="处理中" value="in_progress" />
          <el-option label="已修复" value="fixed" />
          <el-option label="测试中" value="testing" />
          <el-option label="已关闭" value="closed" />
          <el-option label="重新打开" value="reopened" />
        </el-select>
        <el-select
          v-model="filters.severity"
          placeholder="严重程度"
          clearable
          @change="fetchTopics"
          style="width: 120px"
        >
          <el-option label="低" value="low" />
          <el-option label="中" value="medium" />
          <el-option label="高" value="high" />
          <el-option label="严重" value="critical" />
        </el-select>
        <el-select
          v-model="filters.assigned_to"
          placeholder="负责人"
          clearable
          @change="fetchTopics"
          style="width: 150px"
        >
          <el-option
            v-for="user in users"
            :key="user.id"
            :label="user.full_name"
            :value="user.id"
          />
        </el-select>
        <el-button type="primary" @click="fetchTopics">搜索</el-button>
      </div>

      <el-table :data="topics" style="width: 100%; margin-top: 20px" v-loading="loading">
        <el-table-column prop="topic_number" label="课题号" width="150" />
        <el-table-column prop="title" label="课题标题" min-width="200" />
        <el-table-column label="项目" width="120">
          <template #default="{ row }">
            {{ getProjectName(row.project_id) }}
          </template>
        </el-table-column>
        <el-table-column label="创建人" width="100">
          <template #default="{ row }">
            {{ getUserName(row.created_by) }}
          </template>
        </el-table-column>
        <el-table-column label="负责人" width="100">
          <template #default="{ row }">
            {{ getUserName(row.assigned_to) || "未分配" }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)">
              {{ getSeverityLabel(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="120">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button text :icon="View" @click="handleView(row)"
              >详情</el-button
            >

            <!-- 负责人修复后提交复测 -->
            <el-button
              v-if="
                row.assigned_to === currentUserId &&
                row.status === 'in_progress'
              "
              type="success"
              text
              @click="handleSubmitRetest(row)"
            >
              修复提测
            </el-button>

            <!-- 创建者进行复测操作 -->
            <el-dropdown
              v-if="
                row.created_by === currentUserId && row.status === 'testing'
              "
              @command="(cmd) => handleRetestAction(cmd, row)"
            >
              <el-button type="warning" text>
                复测<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="pass"
                    >✓ 通过并关闭</el-dropdown-item
                  >
                  <el-dropdown-item command="fail">✗ 失败打回</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>

            <!-- 管理员或创建者可以删除 -->
            <el-button
              v-if="isAdmin || row.created_by === currentUserId"
              text
              type="danger"
              :icon="Delete"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑课题对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form
        :model="topicForm"
        :rules="rules"
        ref="formRef"
        label-width="100px"
      >
        <el-form-item label="课题标题" prop="title">
          <el-input v-model="topicForm.title" />
        </el-form-item>
        <el-form-item label="课题描述" prop="description">
          <el-input v-model="topicForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="复现步骤">
          <el-input
            v-model="topicForm.steps_to_reproduce"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="所属项目" prop="project_id">
          <el-select
            v-model="topicForm.project_id"
            placeholder="选择项目"
            style="width: 100%"
            :disabled="isEdit"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-select
            v-model="topicForm.assigned_to"
            placeholder="选择负责人"
            clearable
            style="width: 100%"
            :disabled="!topicForm.project_id"
          >
            <el-option
              v-for="user in availableUsers"
              :key="user.id"
              :label="`${user.full_name} (${user.username})`"
              :value="user.id"
            />
          </el-select>
          <div
            v-if="!topicForm.project_id"
            style="color: #999; font-size: 12px; margin-top: 5px"
          >
            请先选择所属项目
          </div>
          <div
            v-else-if="availableUsers.length === 0"
            style="color: #f56c6c; font-size: 12px; margin-top: 5px"
          >
            该项目暂无团队成员
          </div>
        </el-form-item>
        <el-form-item label="严重程度" prop="severity">
          <el-radio-group v-model="topicForm.severity">
            <el-radio label="low">低</el-radio>
            <el-radio label="medium">中</el-radio>
            <el-radio label="high">高</el-radio>
            <el-radio label="critical">严重</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="状态" v-if="isEdit">
          <el-select v-model="topicForm.status" style="width: 100%">
            <el-option label="打开" value="open" />
            <el-option label="已分配" value="assigned" />
            <el-option label="处理中" value="in_progress" />
            <el-option label="已修复" value="fixed" />
          </el-select>
        </el-form-item>
        <el-form-item label="修复说明" v-if="isEdit">
          <el-input
            v-model="topicForm.fix_description"
            type="textarea"
            :rows="3"
          />
        </el-form-item>

        <!-- 课题截图上传 -->
        <el-form-item label="课题截图">
          <el-upload
            :auto-upload="false"
            :on-change="handletopicImageChange"
            :file-list="topicImageFileList"
            :on-remove="handletopicImageRemove"
            list-type="picture-card"
            accept="image/*"
            multiple
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">支持jpg、png、gif格式，最多上传5张</div>
        </el-form-item>

        <!-- 修复截图上传（仅编辑时显示） -->
        <el-form-item label="修复截图" v-if="isEdit">
          <el-upload
            :auto-upload="false"
            :on-change="handleFixImageChange"
            :file-list="fixImageFileList"
            :on-remove="handleFixImageRemove"
            list-type="picture-card"
            accept="image/*"
            multiple
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">上传修复后的截图</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting"
          >确定</el-button
        >
      </template>
    </el-dialog>

    <!-- 课题详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="课题详情" width="700px">
      <div v-if="currentTopic" class="topic-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="标题">{{
            currentTopic.title
          }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentTopic.status)">
              {{ getStatusLabel(currentTopic.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="严重程度">
            <el-tag :type="getSeverityType(currentTopic.severity)">
              {{ getSeverityLabel(currentTopic.severity) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="负责人">
            {{ getUserName(currentTopic.assigned_to) || "未分配" }}
          </el-descriptions-item>
          <el-descriptions-item label="创建人">
            {{ getUserName(currentTopic.created_by) }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(currentTopic.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentTopic.description }}
          </el-descriptions-item>
          <el-descriptions-item label="复现步骤" :span="2">
            {{ currentTopic.steps_to_reproduce || "无" }}
          </el-descriptions-item>
          <el-descriptions-item label="修复说明" :span="2">
            {{ currentTopic.fix_description || "无" }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="attachments-section">
          <h3>附件</h3>
          <el-upload
            :action="`/api/topics/${currentTopic.id}/upload`"
            :headers="{ Authorization: `Bearer ${token}` }"
            :on-success="handleUploadSuccess"
            :show-file-list="false"
            accept="image/*"
          >
            <el-button type="primary" :icon="Upload">上传图片</el-button>
          </el-upload>

          <div class="attachment-list">
            <div
              v-for="(attachment, index) in currentTopic.attachments"
              :key="index"
              class="attachment-item"
            >
              <el-image
                :src="`/uploads/${attachment}`"
                :preview-src-list="
                  currentTopic.attachments.map((a) => `/uploads/${a}`)
                "
                :initial-index="index"
                fit="cover"
                style="width: 100px; height: 100px"
              />
            </div>
          </div>
        </div>

        <!-- 评论区域 -->
        <div class="comments-section">
          <h3>讨论交流</h3>

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
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from "vue";
import { useRouter } from "vue-router";
import { topicAPI, projectAPI, userAPI } from "@/api";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Plus,
  Edit,
  Delete,
  View,
  Upload,
  ArrowDown,
  Search,
} from "@element-plus/icons-vue";
import { useUserStore } from "@/stores/user";
import { useNotificationStore } from "@/stores/notification";
import dayjs from "dayjs";

const router = useRouter();
const userStore = useUserStore();
const notificationStore = useNotificationStore();
const topics = ref([]);
const projects = ref([]);
const users = ref([]);
const dialogVisible = ref(false);
const detailDialogVisible = ref(false);
const formRef = ref();
const submitting = ref(false);
const isEdit = ref(false);
const currentTopic = ref(null);
const token = localStorage.getItem("token");
const loading = ref(false);

// 评论相关
const comments = ref([]);
const commentContent = ref("");

// 图片上传相关
const topicImageFileList = ref([]);
const fixImageFileList = ref([]);

// 当前用户信息
const currentUserId = computed(() => userStore.userId);
const isAdmin = computed(() => userStore.isAdmin);

const filters = reactive({
  project_id: "",
  status: "",
  assigned_to: "",
  severity: "",
  keyword: "",
});

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  total_pages: 0,
});

const topicForm = reactive({
  title: "",
  description: "",
  steps_to_reproduce: "",
  project_id: "",
  assigned_to: "",
  severity: "medium",
  status: "open",
  fix_description: "",
});

const rules = {
  title: [{ required: true, message: "请输入课题标题", trigger: "blur" }],
  description: [{ required: true, message: "请输入课题描述", trigger: "blur" }],
  project_id: [{ required: true, message: "请选择项目", trigger: "change" }],
  severity: [{ required: true, message: "请选择严重程度", trigger: "change" }],
};

const dialogTitle = computed(() => (isEdit.value ? "编辑课题" : "创建课题"));

const fetchTopics = async () => {
  try {
    loading.value = true;
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
    };
    if (filters.project_id) params.project_id = filters.project_id;
    if (filters.status) params.status = filters.status;
    if (filters.assigned_to) params.assigned_to = filters.assigned_to;
    if (filters.severity) params.severity = filters.severity;
    if (filters.keyword) params.keyword = filters.keyword;
    
    const response = await topicAPI.getTopics(params);
    topics.value = response.items || [];
    pagination.total = response.total || 0;
    pagination.total_pages = response.total_pages || 0;
  } catch (error) {
    ElMessage.error("获取课题列表失败");
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (page) => {
  pagination.page = page;
  fetchTopics();
};

const handleSizeChange = (size) => {
  pagination.page_size = size;
  pagination.page = 1;
  fetchTopics();
};

const fetchProjects = async () => {
  try {
    const data = await projectAPI.getProjects({ limit: 100 }); // 下拉框获取更多项目
    projects.value = data.items || [];
  } catch (error) {
    ElMessage.error("获取项目列表失败");
  }
};

const fetchUsers = async () => {
  try {
    users.value = await userAPI.getUsers();
  } catch (error) {
    ElMessage.error("获取用户列表失败");
  }
};

// 根据选择的项目过滤可用的负责人
const availableUsers = computed(() => {
  if (!topicForm.project_id) {
    return [];
  }
  const selectedProject = projects.value.find(
    (p) => p.id === topicForm.project_id
  );
  if (!selectedProject || !selectedProject.team_members) {
    return [];
  }
  // 只返回该项目的团队成员
  return users.value.filter((user) =>
    selectedProject.team_members.includes(user.id)
  );
});

// 图片转base64
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = (error) => reject(error);
  });
};

const handletopicImageChange = (file, fileList) => {
  // 限制最多5张
  if (fileList.length > 5) {
    ElMessage.warning("最多只能上传5张图片");
    topicImageFileList.value = fileList.slice(0, 5);
  } else {
    topicImageFileList.value = fileList;
  }
};

const handletopicImageRemove = (file, fileList) => {
  topicImageFileList.value = fileList;
};

const handleFixImageChange = (file, fileList) => {
  if (fileList.length > 5) {
    ElMessage.warning("最多只能上传5张图片");
    fixImageFileList.value = fileList.slice(0, 5);
  } else {
    fixImageFileList.value = fileList;
  }
};

const handleFixImageRemove = (file, fileList) => {
  fixImageFileList.value = fileList;
};

const showCreateDialog = () => {
  isEdit.value = false;
  Object.assign(topicForm, {
    title: "",
    description: "",
    steps_to_reproduce: "",
    project_id: filters.project_id || "",
    assigned_to: "",
    severity: "medium",
    status: "open",
    fix_description: "",
  });
  topicImageFileList.value = [];
  fixImageFileList.value = [];
  dialogVisible.value = true;
};

const handleEdit = (topic) => {
  isEdit.value = true;
  currentTopic.value = topic;
  Object.assign(topicForm, {
    title: topic.title,
    description: topic.description,
    steps_to_reproduce: topic.steps_to_reproduce,
    project_id: topic.project_id,
    assigned_to: topic.assigned_to,
    severity: topic.severity,
    status: topic.status,
    fix_description: topic.fix_description,
  });

  // 显示已有图片
  topicImageFileList.value = topic.topic_images
    ? topic.topic_images.map((img, index) => ({
        name: `topic_image_${index}`,
        url: img,
        uid: -1 - index,
      }))
    : [];

  fixImageFileList.value = topic.fix_images
    ? topic.fix_images.map((img, index) => ({
        name: `fix_image_${index}`,
        url: img,
        uid: -1000 - index,
      }))
    : [];

  dialogVisible.value = true;
};

const handleView = (topic) => {
  router.push(`/topics/${topic.id}`);
};

// 获取评论列表
const fetchComments = async (topicId) => {
  try {
    comments.value = await topicAPI.getComments(topicId);
  } catch (error) {
    console.error("获取评论失败:", error);
  }
};

// 添加评论
const handleAddComment = async () => {
  if (!commentContent.value.trim()) {
    return;
  }

  try {
    await topicAPI.addComment(currentTopic.value.id, {
      content: commentContent.value.trim(),
    });
    ElMessage.success("评论发表成功");
    commentContent.value = "";
    // 刷新评论列表
    await fetchComments(currentTopic.value.id);
    // 刷新通知（通知相关人员）
    notificationStore.fetchUnreadCount();
  } catch (error) {
    ElMessage.error("发表评论失败");
  }
};

const handleSubmit = async () => {
  const valid = await formRef.value.validate();
  if (!valid) return;

  submitting.value = true;
  try {
    // 处理课题截图
    const topicImages = [];
    for (const file of topicImageFileList.value) {
      if (file.raw) {
        // 新上传的文件，转换为base64
        const base64 = await fileToBase64(file.raw);
        topicImages.push(base64);
      } else if (file.url) {
        // 已有的图片，保持原样
        topicImages.push(file.url);
      }
    }

    // 处理修复截图
    const fixImages = [];
    for (const file of fixImageFileList.value) {
      if (file.raw) {
        const base64 = await fileToBase64(file.raw);
        fixImages.push(base64);
      } else if (file.url) {
        fixImages.push(file.url);
      }
    }

    const submitData = {
      ...topicForm,
      topic_images: topicImages,
      fix_images: fixImages,
    };

    if (isEdit.value) {
      await topicAPI.updateTopic(currentTopic.value.id, submitData);
      ElMessage.success("topic更新成功");
    } else {
      await topicAPI.createTopic(submitData);
      ElMessage.success("topic创建成功");
    }
    dialogVisible.value = false;
    fetchTopics();
    // 立即刷新通知
    notificationStore.fetchUnreadCount();
  } catch (error) {
    console.error("Submit error:", error);
    ElMessage.error("操作失败");
  } finally {
    submitting.value = false;
  }
};

// 开发人员修复提测
const handleSubmitRetest = async (topic) => {
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
    await topicAPI.startRetest(topic.id);
    ElMessage.success("已提交复测，等待创建者验证");
    fetchTopics();
    // 立即刷新通知（通知创建者）
    notificationStore.fetchUnreadCount();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("提交失败");
    }
  }
};

// 创建者进行复测操作
const handleRetestAction = async (command, topic) => {
  try {
    if (command === "pass") {
      // 复测通过
      await ElMessageBox.confirm(
        "确认课题已修复，通过复测并关闭？",
        "复测通过",
        {
          type: "success",
          confirmButtonText: "确认通过",
          cancelButtonText: "取消",
        }
      );
      await topicAPI.closeTopic(topic.id);
      ElMessage.success("复测通过，课题已关闭");
    } else if (command === "fail") {
      // 复测失败
      await ElMessageBox.confirm(
        '确认课题未修复，打回重新处理？topic将退回至"已分配"状态，负责人需重新接收。',
        "复测失败",
        {
          type: "warning",
          confirmButtonText: "确认打回",
          cancelButtonText: "取消",
        }
      );
      await topicAPI.reopenTopic(topic.id);
      ElMessage.warning('课题已打回至"已分配"状态，负责人需重新接收处理');
    }
    fetchTopics();
    // 立即刷新通知（通知负责人或创建者）
    notificationStore.fetchUnreadCount();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("操作失败");
    }
  }
};

// 删除topic
const handleDelete = async (topic) => {
  try {
    await ElMessageBox.confirm(
      "确定要删除这个课题吗？删除后无法恢复。",
      "删除确认",
      {
        type: "warning",
        confirmButtonText: "确认删除",
        cancelButtonText: "取消",
      }
    );
    await topicAPI.deleteTopic(topic.id);
    ElMessage.success("删除成功");
    fetchTopics();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
};

const handleUploadSuccess = () => {
  ElMessage.success("上传成功");
  handleView(currentTopic.value);
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

const formatDate = (date) => {
  return dayjs(date).format("YYYY-MM-DD");
};

const formatDateTime = (date) => {
  return dayjs(date).format("YYYY-MM-DD HH:mm:ss");
};

// 监听项目变化，如果当前负责人不在新项目的团队成员中，则清空
watch(
  () => topicForm.project_id,
  (newProjectId, oldProjectId) => {
    // 只在项目真正改变时处理
    if (newProjectId !== oldProjectId && topicForm.assigned_to) {
      const selectedProject = projects.value.find((p) => p.id === newProjectId);
      if (selectedProject && selectedProject.team_members) {
        // 如果当前选择的负责人不在新项目的团队成员中，清空负责人
        if (!selectedProject.team_members.includes(topicForm.assigned_to)) {
          topicForm.assigned_to = "";
          ElMessage.warning("所选负责人不在该项目团队中，已自动清空");
        }
      }
    }
  }
);

onMounted(() => {
  fetchTopics();
  fetchProjects();
  fetchUsers();
});
</script>

<style scoped>
.topics {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filter-bar {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.topic-detail {
  padding: 10px 0;
}

.attachments-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.attachments-section h3 {
  margin-bottom: 15px;
}

.attachment-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 15px;
}

.attachment-item {
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}

.comments-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.comments-section h3 {
  margin-bottom: 20px;
  color: #333;
  font-size: 16px;
}

.comment-input {
  margin-bottom: 25px;
}

.comments-list {
  max-height: 400px;
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

.upload-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
}
</style>

