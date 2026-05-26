<template>
  <div class="bugs">
    <div class="page-header">
      <h1>BUG管理</h1>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog">创建BUG</el-button>
    </div>

    <el-card>
      <div class="filter-bar">
        <el-select v-model="filters.project_id" placeholder="选择项目" clearable @change="fetchBugs" style="width: 200px">
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>
        <el-select v-model="filters.status" placeholder="BUG状态" clearable @change="fetchBugs" style="width: 150px">
          <el-option label="打开" value="open" />
          <el-option label="已分配" value="assigned" />
          <el-option label="处理中" value="in_progress" />
          <el-option label="已修复" value="fixed" />
          <el-option label="测试中" value="testing" />
          <el-option label="已关闭" value="closed" />
          <el-option label="重新打开" value="reopened" />
        </el-select>
        <el-select v-model="filters.assigned_to" placeholder="负责人" clearable @change="fetchBugs" style="width: 150px">
          <el-option
            v-for="user in users"
            :key="user.id"
            :label="user.full_name"
            :value="user.id"
          />
        </el-select>
      </div>

      <el-table :data="bugs" style="width: 100%; margin-top: 20px">
        <el-table-column prop="title" label="BUG标题" min-width="200" />
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
            {{ getUserName(row.assigned_to) || '未分配' }}
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
            <el-button text :icon="View" @click="handleView(row)">详情</el-button>
            
            <!-- 负责人修复后提交复测 -->
            <el-button 
              v-if="row.assigned_to === currentUserId && row.status === 'in_progress'" 
              type="success" 
              text 
              @click="handleSubmitRetest(row)"
            >
              修复提测
            </el-button>
            
            <!-- 创建者进行复测操作 -->
            <el-dropdown 
              v-if="row.created_by === currentUserId && row.status === 'testing'" 
              @command="(cmd) => handleRetestAction(cmd, row)"
            >
              <el-button type="warning" text>
                复测<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="pass">✓ 通过并关闭</el-dropdown-item>
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
    </el-card>

    <!-- 创建/编辑BUG对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
    >
      <el-form :model="bugForm" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="BUG标题" prop="title">
          <el-input v-model="bugForm.title" />
        </el-form-item>
        <el-form-item label="BUG描述" prop="description">
          <el-input v-model="bugForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="复现步骤">
          <el-input v-model="bugForm.steps_to_reproduce" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="所属项目" prop="project_id">
          <el-select v-model="bugForm.project_id" placeholder="选择项目" style="width: 100%" :disabled="isEdit">
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-select v-model="bugForm.assigned_to" placeholder="选择负责人" clearable style="width: 100%">
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="`${user.full_name} (${user.username})`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="严重程度" prop="severity">
          <el-radio-group v-model="bugForm.severity">
            <el-radio label="low">低</el-radio>
            <el-radio label="medium">中</el-radio>
            <el-radio label="high">高</el-radio>
            <el-radio label="critical">严重</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="状态" v-if="isEdit">
          <el-select v-model="bugForm.status" style="width: 100%">
            <el-option label="打开" value="open" />
            <el-option label="已分配" value="assigned" />
            <el-option label="处理中" value="in_progress" />
            <el-option label="已修复" value="fixed" />
          </el-select>
        </el-form-item>
        <el-form-item label="修复说明" v-if="isEdit">
          <el-input v-model="bugForm.fix_description" type="textarea" :rows="3" />
        </el-form-item>
        
        <!-- BUG截图上传 -->
        <el-form-item label="BUG截图">
          <el-upload
            :auto-upload="false"
            :on-change="handleBugImageChange"
            :file-list="bugImageFileList"
            :on-remove="handleBugImageRemove"
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
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- BUG详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="BUG详情"
      width="700px"
    >
      <div v-if="currentBug" class="bug-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="标题">{{ currentBug.title }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentBug.status)">
              {{ getStatusLabel(currentBug.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="严重程度">
            <el-tag :type="getSeverityType(currentBug.severity)">
              {{ getSeverityLabel(currentBug.severity) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="负责人">
            {{ getUserName(currentBug.assigned_to) || '未分配' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建人">
            {{ getUserName(currentBug.created_by) }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(currentBug.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentBug.description }}
          </el-descriptions-item>
          <el-descriptions-item label="复现步骤" :span="2">
            {{ currentBug.steps_to_reproduce || '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="修复说明" :span="2">
            {{ currentBug.fix_description || '无' }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="attachments-section">
          <h3>附件</h3>
          <el-upload
            :action="`/api/bugs/${currentBug.id}/upload`"
            :headers="{ Authorization: `Bearer ${token}` }"
            :on-success="handleUploadSuccess"
            :show-file-list="false"
            accept="image/*"
          >
            <el-button type="primary" :icon="Upload">上传图片</el-button>
          </el-upload>
          
          <div class="attachment-list">
            <div v-for="(attachment, index) in currentBug.attachments" :key="index" class="attachment-item">
              <el-image
                :src="`/uploads/${attachment}`"
                :preview-src-list="currentBug.attachments.map(a => `/uploads/${a}`)"
                :initial-index="index"
                fit="cover"
                style="width: 100px; height: 100px;"
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
              style="margin-top: 10px;"
            >
              发表评论
            </el-button>
          </div>

          <!-- 评论列表 -->
          <div class="comments-list">
            <el-empty v-if="comments.length === 0" description="暂无评论" />
            <div v-for="comment in comments" :key="comment.id" class="comment-item">
              <div class="comment-header">
                <span class="comment-user">{{ comment.user_name }}</span>
                <span class="comment-time">{{ formatDateTime(comment.created_at) }}</span>
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
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { bugAPI, projectAPI, userAPI } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, View, Upload, ArrowDown } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useNotificationStore } from '@/stores/notification'
import dayjs from 'dayjs'

const router = useRouter()
const userStore = useUserStore()
const notificationStore = useNotificationStore()
const bugs = ref([])
const projects = ref([])
const users = ref([])
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const formRef = ref()
const submitting = ref(false)
const isEdit = ref(false)
const currentBug = ref(null)
const token = localStorage.getItem('token')

// 评论相关
const comments = ref([])
const commentContent = ref('')

// 图片上传相关
const bugImageFileList = ref([])
const fixImageFileList = ref([])

// 当前用户信息
const currentUserId = computed(() => userStore.userId)
const isAdmin = computed(() => userStore.isAdmin)

const filters = reactive({
  project_id: '',
  status: '',
  assigned_to: ''
})

const bugForm = reactive({
  title: '',
  description: '',
  steps_to_reproduce: '',
  project_id: '',
  assigned_to: '',
  severity: 'medium',
  status: 'open',
  fix_description: ''
})

const rules = {
  title: [{ required: true, message: '请输入BUG标题', trigger: 'blur' }],
  description: [{ required: true, message: '请输入BUG描述', trigger: 'blur' }],
  project_id: [{ required: true, message: '请选择项目', trigger: 'change' }],
  severity: [{ required: true, message: '请选择严重程度', trigger: 'change' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑BUG' : '创建BUG')

const fetchBugs = async () => {
  try {
    const params = {}
    if (filters.project_id) params.project_id = filters.project_id
    if (filters.status) params.status = filters.status
    if (filters.assigned_to) params.assigned_to = filters.assigned_to
    bugs.value = await bugAPI.getBugs(params)
  } catch (error) {
    ElMessage.error('获取BUG列表失败')
  }
}

const fetchProjects = async () => {
  try {
    projects.value = await projectAPI.getProjects()
  } catch (error) {
    ElMessage.error('获取项目列表失败')
  }
}

const fetchUsers = async () => {
  try {
    users.value = await userAPI.getUsers()
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  }
}

// 图片转base64
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => resolve(reader.result)
    reader.onerror = error => reject(error)
  })
}

const handleBugImageChange = (file, fileList) => {
  // 限制最多5张
  if (fileList.length > 5) {
    ElMessage.warning('最多只能上传5张图片')
    bugImageFileList.value = fileList.slice(0, 5)
  } else {
    bugImageFileList.value = fileList
  }
}

const handleBugImageRemove = (file, fileList) => {
  bugImageFileList.value = fileList
}

const handleFixImageChange = (file, fileList) => {
  if (fileList.length > 5) {
    ElMessage.warning('最多只能上传5张图片')
    fixImageFileList.value = fileList.slice(0, 5)
  } else {
    fixImageFileList.value = fileList
  }
}

const handleFixImageRemove = (file, fileList) => {
  fixImageFileList.value = fileList
}

const showCreateDialog = () => {
  isEdit.value = false
  Object.assign(bugForm, {
    title: '',
    description: '',
    steps_to_reproduce: '',
    project_id: filters.project_id || '',
    assigned_to: '',
    severity: 'medium',
    status: 'open',
    fix_description: ''
  })
  bugImageFileList.value = []
  fixImageFileList.value = []
  dialogVisible.value = true
}

const handleEdit = (bug) => {
  isEdit.value = true
  currentBug.value = bug
  Object.assign(bugForm, {
    title: bug.title,
    description: bug.description,
    steps_to_reproduce: bug.steps_to_reproduce,
    project_id: bug.project_id,
    assigned_to: bug.assigned_to,
    severity: bug.severity,
    status: bug.status,
    fix_description: bug.fix_description
  })
  
  // 显示已有图片
  bugImageFileList.value = bug.bug_images ? bug.bug_images.map((img, index) => ({
    name: `bug_image_${index}`,
    url: img,
    uid: -1 - index
  })) : []
  
  fixImageFileList.value = bug.fix_images ? bug.fix_images.map((img, index) => ({
    name: `fix_image_${index}`,
    url: img,
    uid: -1000 - index
  })) : []
  
  dialogVisible.value = true
}

const handleView = (bug) => {
  router.push(`/bugs/${bug.id}`)
}

// 获取评论列表
const fetchComments = async (bugId) => {
  try {
    comments.value = await bugAPI.getComments(bugId)
  } catch (error) {
    console.error('获取评论失败:', error)
  }
}

// 添加评论
const handleAddComment = async () => {
  if (!commentContent.value.trim()) {
    return
  }
  
  try {
    await bugAPI.addComment(currentBug.value.id, {
      content: commentContent.value.trim()
    })
    ElMessage.success('评论发表成功')
    commentContent.value = ''
    // 刷新评论列表
    await fetchComments(currentBug.value.id)
    // 刷新通知（通知相关人员）
    notificationStore.fetchUnreadCount()
  } catch (error) {
    ElMessage.error('发表评论失败')
  }
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate()
  if (!valid) return
  
  submitting.value = true
  try {
    // 处理BUG截图
    const bugImages = []
    for (const file of bugImageFileList.value) {
      if (file.raw) {
        // 新上传的文件，转换为base64
        const base64 = await fileToBase64(file.raw)
        bugImages.push(base64)
      } else if (file.url) {
        // 已有的图片，保持原样
        bugImages.push(file.url)
      }
    }
    
    // 处理修复截图
    const fixImages = []
    for (const file of fixImageFileList.value) {
      if (file.raw) {
        const base64 = await fileToBase64(file.raw)
        fixImages.push(base64)
      } else if (file.url) {
        fixImages.push(file.url)
      }
    }
    
    const submitData = {
      ...bugForm,
      bug_images: bugImages,
      fix_images: fixImages
    }
    
    if (isEdit.value) {
      await bugAPI.updateBug(currentBug.value.id, submitData)
      ElMessage.success('BUG更新成功')
    } else {
      await bugAPI.createBug(submitData)
      ElMessage.success('BUG创建成功')
    }
    dialogVisible.value = false
    fetchBugs()
    // 立即刷新通知
    notificationStore.fetchUnreadCount()
  } catch (error) {
    console.error('Submit error:', error)
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

// 开发人员修复提测
const handleSubmitRetest = async (bug) => {
  try {
    await ElMessageBox.confirm(
      '确认BUG已修复并提交复测？提交后将通知创建者进行验证。', 
      '修复提测', 
      { 
        type: 'success',
        confirmButtonText: '确认提交',
        cancelButtonText: '取消'
      }
    )
    await bugAPI.startRetest(bug.id)
    ElMessage.success('已提交复测，等待创建者验证')
    fetchBugs()
    // 立即刷新通知（通知创建者）
    notificationStore.fetchUnreadCount()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('提交失败')
    }
  }
}

// 创建者进行复测操作
const handleRetestAction = async (command, bug) => {
  try {
    if (command === 'pass') {
      // 复测通过
      await ElMessageBox.confirm(
        '确认BUG已修复，通过复测并关闭？', 
        '复测通过', 
        { 
          type: 'success',
          confirmButtonText: '确认通过',
          cancelButtonText: '取消'
        }
      )
      await bugAPI.closeBug(bug.id)
      ElMessage.success('复测通过，BUG已关闭')
    } else if (command === 'fail') {
      // 复测失败
      await ElMessageBox.confirm(
        '确认BUG未修复，打回重新处理？BUG将退回至"已分配"状态，负责人需重新接收。', 
        '复测失败', 
        { 
          type: 'warning',
          confirmButtonText: '确认打回',
          cancelButtonText: '取消'
        }
      )
      await bugAPI.reopenBug(bug.id)
      ElMessage.warning('BUG已打回至"已分配"状态，负责人需重新接收处理')
    }
    fetchBugs()
    // 立即刷新通知（通知负责人或创建者）
    notificationStore.fetchUnreadCount()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

// 删除BUG
const handleDelete = async (bug) => {
  try {
    await ElMessageBox.confirm('确定要删除这个BUG吗？删除后无法恢复。', '删除确认', { 
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消'
    })
    await bugAPI.deleteBug(bug.id)
    ElMessage.success('删除成功')
    fetchBugs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleUploadSuccess = () => {
  ElMessage.success('上传成功')
  handleView(currentBug.value)
}

const getProjectName = (projectId) => {
  const project = projects.value.find(p => p.id === projectId)
  return project ? project.name : '未知项目'
}

const getUserName = (userId) => {
  if (!userId) return null
  const user = users.value.find(u => u.id === userId)
  return user ? user.full_name : '未知用户'
}

const getStatusType = (status) => {
  const types = {
    open: 'info',
    assigned: 'warning',
    in_progress: 'warning',
    fixed: 'success',
    testing: 'warning',
    closed: 'success',
    reopened: 'danger'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status) => {
  const labels = {
    open: '打开',
    assigned: '已分配',
    in_progress: '处理中',
    fixed: '已修复',
    testing: '测试中',
    closed: '已关闭',
    reopened: '重新打开'
  }
  return labels[status] || status
}

const getSeverityType = (severity) => {
  const types = {
    low: 'info',
    medium: '',
    high: 'warning',
    critical: 'danger'
  }
  return types[severity] || ''
}

const getSeverityLabel = (severity) => {
  const labels = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '严重'
  }
  return labels[severity] || severity
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD')
}

const formatDateTime = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

onMounted(() => {
  fetchBugs()
  fetchProjects()
  fetchUsers()
})
</script>

<style scoped>
.bugs {
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

.bug-detail {
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
  color: #409EFF;
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

