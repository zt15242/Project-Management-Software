<template>
  <div class="notifications">
    <div class="page-header">
      <h1>通知中心</h1>
      <el-button @click="notificationStore.markAllAsRead" :disabled="notificationStore.unreadCount === 0">
        全部标记为已读
      </el-button>
    </div>

    <el-card>
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="全部通知" name="all" />
        <el-tab-pane label="未读通知" name="unread" />
      </el-tabs>

      <div v-if="notificationStore.notifications.length === 0" class="empty-state">
        <el-empty description="暂无通知" />
      </div>

      <div v-else class="notification-list">
        <div
          v-for="notification in notificationStore.notifications"
          :key="notification.id"
          :class="['notification-card', { unread: !notification.is_read }]"
          @click="handleNotificationClick(notification)"
        >
          <div class="notification-icon">
            <el-icon :size="24" :color="getNotificationColor(notification.type)">
              <component :is="getNotificationIcon(notification.type)" />
            </el-icon>
          </div>
          <div class="notification-content">
            <div class="notification-header">
              <span class="notification-title">{{ notification.title }}</span>
              <span class="notification-time">{{ formatTime(notification.created_at) }}</span>
            </div>
            <div class="notification-message">{{ notification.message }}</div>
            <div class="notification-footer">
              <el-tag :type="getNotificationTypeTag(notification.type)" size="small">
                {{ getNotificationTypeLabel(notification.type) }}
              </el-tag>
            </div>
          </div>
          <div class="notification-actions">
            <el-button
              v-if="!notification.is_read"
              circle
              size="small"
              @click.stop="notificationStore.markAsRead(notification.id)"
            >
              <el-icon><Check /></el-icon>
            </el-button>
            <el-button
              circle
              size="small"
              type="danger"
              @click.stop="notificationStore.deleteNotification(notification.id)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '@/stores/notification'
import { WarningFilled, InfoFilled, SuccessFilled, Check, Delete, Warning, ChatDotRound } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const router = useRouter()
const notificationStore = useNotificationStore()
const activeTab = ref('all')

const handleTabChange = (tab) => {
  notificationStore.fetchNotifications(tab === 'unread')
}

const handleNotificationClick = async (notification) => {
  if (!notification.is_read) {
    await notificationStore.markAsRead(notification.id)
  }
  
  // 根据通知类型跳转
  if (notification.bug_id) {
    router.push(`/bugs?id=${notification.bug_id}`)
  } else if (notification.project_id) {
    router.push(`/projects/${notification.project_id}`)
  }
}

const getNotificationIcon = (type) => {
  const icons = {
    bug_assigned: Warning,
    bug_retest_submitted: InfoFilled,
    bug_reopened: WarningFilled,
    bug_closed: SuccessFilled,
    bug_comment: ChatDotRound,
    default: InfoFilled
  }
  return icons[type] || icons.default
}

const getNotificationColor = (type) => {
  const colors = {
    bug_assigned: '#F56C6C',
    bug_retest_submitted: '#409EFF',
    bug_reopened: '#E6A23C',
    bug_closed: '#67C23A',
    bug_comment: '#909399',
    default: '#409EFF'
  }
  return colors[type] || colors.default
}

const getNotificationTypeTag = (type) => {
  const tags = {
    bug_assigned: 'danger',
    bug_retest_submitted: 'primary',
    bug_reopened: 'warning',
    bug_closed: 'success',
    bug_comment: 'info',
    default: 'info'
  }
  return tags[type] || tags.default
}

const getNotificationTypeLabel = (type) => {
  const labels = {
    bug_assigned: 'BUG分配',
    bug_retest_submitted: '提交复测',
    bug_reopened: 'BUG打回',
    bug_closed: 'BUG关闭',
    bug_comment: 'BUG评论',
    default: '通知'
  }
  return labels[type] || labels.default
}

const formatTime = (time) => {
  return dayjs(time).fromNow()
}

onMounted(() => {
  notificationStore.fetchNotifications()
})
</script>

<style scoped>
.notifications {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.notification-list {
  margin-top: 20px;
}

.notification-card {
  display: flex;
  align-items: flex-start;
  padding: 20px;
  margin-bottom: 15px;
  background: #f9f9f9;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border-left: 3px solid transparent;
}

.notification-card:hover {
  background: #f0f0f0;
  transform: translateX(5px);
}

.notification-card.unread {
  background: #e6f7ff;
  border-left-color: #409EFF;
}

.notification-icon {
  margin-right: 15px;
  margin-top: 5px;
}

.notification-content {
  flex: 1;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.notification-title {
  font-weight: bold;
  font-size: 16px;
  color: #333;
}

.notification-time {
  color: #999;
  font-size: 12px;
}

.notification-message {
  color: #666;
  margin-bottom: 10px;
  line-height: 1.5;
}

.notification-footer {
  display: flex;
  align-items: center;
}

.notification-actions {
  display: flex;
  gap: 10px;
  margin-left: 15px;
}

.empty-state {
  padding: 50px 0;
  text-align: center;
}
</style>

