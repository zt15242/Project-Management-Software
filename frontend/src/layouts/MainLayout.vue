<template>
  <el-container class="main-layout">
    <el-aside width="200px" class="sidebar">
      <div class="logo">
        <h2>项目管理系统</h2>
      </div>
      <el-menu
        :key="userStore.user?.role"
        :default-active="activeMenu"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard" v-if="!userStore.isExternal">
          <el-icon><DataAnalysis /></el-icon>
          <span>控制台</span>
        </el-menu-item>
        <el-menu-item index="/projects" v-if="!userStore.isExternal">
          <el-icon><Folder /></el-icon>
          <span>项目</span>
        </el-menu-item>
        <el-menu-item index="/tasks" v-if="!userStore.isExternal">
          <el-icon><List /></el-icon>
          <span>任务</span>
        </el-menu-item>
        <el-menu-item index="/topics">
          <el-icon><Warning /></el-icon>
          <span>课题</span>
        </el-menu-item>
        <el-menu-item index="/bi" v-if="!userStore.isExternal">
          <el-icon><TrendCharts /></el-icon>
          <span>BI分析</span>
        </el-menu-item>
        <el-menu-item index="/deployments" v-if="!userStore.isExternal">
          <el-icon><Upload /></el-icon>
          <span>代码发布</span>
        </el-menu-item>
        <el-menu-item index="/daily-report" v-if="!userStore.isExternal">
          <el-icon><Calendar /></el-icon>
          <span>工作日报</span>
        </el-menu-item>
        <el-menu-item index="/users" v-if="userStore.isAdmin">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/ai-config" v-if="userStore.isAdmin">
          <el-icon><Setting /></el-icon>
          <span>AI配置</span>
        </el-menu-item>
        <el-menu-item index="/asr-config" v-if="userStore.isAdmin">
          <el-icon><Microphone /></el-icon>
          <span>语音识别配置</span>
        </el-menu-item>
        <el-menu-item index="/email-config" v-if="userStore.isAdmin">
          <el-icon><Postcard /></el-icon>
          <span>邮局配置</span>
        </el-menu-item>
        <el-menu-item index="/background-tasks" v-if="!userStore.isExternal">
          <el-icon><Monitor /></el-icon>
          <span>后台任务</span>
        </el-menu-item>
      </el-menu>
      <div v-if="userStore.isAdmin" class="version-entry" @click="openVersionPopover">
        <span class="version-text">{{ versionInfo.version || 'v0.0.0' }}</span>
        <span :class="['version-dot', versionStatusClass]"></span>
      </div>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.meta.title">{{
              route.meta.title
            }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-badge
            :value="notificationStore.unreadCount"
            :hidden="notificationStore.unreadCount === 0"
            class="notification-badge"
          >
            <el-button :icon="Bell" circle @click="showNotifications" />
          </el-badge>
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :icon="UserFilled" />
              <span class="username">{{ userStore.user?.full_name }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout" divided
                  >退出登录</el-dropdown-item
                >
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>

    <!-- 通知抽屉 -->
    <el-drawer v-model="notificationDrawer" title="通知" size="400px">
      <div class="notification-header">
        <el-button
          text
          @click="notificationStore.markAllAsRead"
          :disabled="notificationStore.unreadCount === 0"
        >
          全部已读
        </el-button>
      </div>
      <el-scrollbar height="calc(100vh - 120px)">
        <div
          v-if="notificationStore.notifications.length === 0"
          class="empty-notifications"
        >
          <el-empty description="暂无通知" />
        </div>
        <div v-else class="notification-list">
          <div
            v-for="notification in notificationStore.notifications"
            :key="notification.id"
            :class="['notification-item', { unread: !notification.is_read }]"
            @click="handleNotificationClick(notification)"
          >
            <div class="notification-content">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-message">{{ notification.message }}</div>
              <div class="notification-time">
                {{ formatTime(notification.created_at) }}
              </div>
            </div>
            <el-button
              :icon="Delete"
              circle
              size="small"
              @click.stop="
                notificationStore.deleteNotification(notification.id)
              "
            />
          </div>
        </div>
      </el-scrollbar>
    </el-drawer>

    <el-dialog v-model="versionDialog" title="当前版本" width="320px" class="version-dialog">
      <div class="version-panel">
        <div class="version-number">{{ versionInfo.version || 'v0.0.0' }}</div>
        <div class="version-state">{{ versionStatusText }}</div>
        <div class="version-meta" v-if="versionInfo.remote_version && versionInfo.remote_version !== versionInfo.version">
          最新版本: {{ versionInfo.remote_version }}
        </div>
        <div class="version-meta" v-if="versionInfo.local_commit">
          当前代码: {{ versionInfo.local_commit }}
        </div>
        <div class="version-meta" v-if="versionInfo.remote_commit">
          远端版本: {{ versionInfo.remote_commit }}
        </div>
        <div class="version-actions">
          <el-button :icon="Refresh" circle @click="fetchVersion" :loading="versionLoading" />
          <el-button
            v-if="versionInfo.has_update && versionInfo.can_update && userStore.isAdmin"
            type="primary"
            @click="handleUpdate"
            :loading="updating"
          >
            更新代码
          </el-button>
          <div v-else-if="versionInfo.has_update" class="version-hint">
            有新版本，请在服务器执行部署脚本更新
          </div>
          <el-button
            v-if="userStore.isAdmin"
            type="success"
            @click="handleRestart"
            :loading="restarting"
          >
            立即重启
          </el-button>
        </div>
      </div>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";
import { useNotificationStore } from "@/stores/notification";
import { systemAPI } from "@/api";
import {
  Bell,
  Delete,
  Refresh,
  UserFilled,
  DataAnalysis,
  Folder,
  List,
  User,
  Warning,
  TrendCharts,
  Upload,
  Setting,
  Calendar,
  Monitor,
  Microphone,
  Postcard,
} from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import "dayjs/locale/zh-cn";

dayjs.extend(relativeTime);
dayjs.locale("zh-cn");

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const notificationStore = useNotificationStore();

const notificationDrawer = ref(false);
const versionDialog = ref(false);
const versionLoading = ref(false);
const updating = ref(false);
const restarting = ref(false);
const versionInfo = ref({});

const activeMenu = computed(() => route.path);

const showNotifications = () => {
  notificationDrawer.value = true;
  notificationStore.fetchNotifications();
};

const handleCommand = (command) => {
  if (command === "logout") {
    userStore.logout();
    notificationStore.stopPolling();
  } else if (command === "profile") {
    router.push("/profile");
  }
};

const handleNotificationClick = async (notification) => {
  if (!notification.is_read) {
    await notificationStore.markAsRead(notification.id);
  }

  // 根据通知类型跳转
  if (notification.topic_id) {
    router.push(`/topics/${notification.topic_id}`);
  } else if (notification.project_id) {
    router.push(`/projects/${notification.project_id}`);
  }

  notificationDrawer.value = false;
};

const formatTime = (time) => {
  return dayjs(time).fromNow();
};

const versionStatusText = computed(() => {
  if (versionInfo.value.status === "update_available") return "发现新版本";
  if (versionInfo.value.status === "restart_required") return "已更新，等待重启";
  return "已是最新版本";
});

const versionStatusClass = computed(() => {
  if (versionInfo.value.status === "update_available") return "warning";
  if (versionInfo.value.status === "restart_required") return "pending";
  return "success";
});

const fetchVersion = async () => {
  versionLoading.value = true;
  try {
    versionInfo.value = await systemAPI.getVersion();
  } finally {
    versionLoading.value = false;
  }
};

const openVersionPopover = () => {
  versionDialog.value = true;
  fetchVersion();
};

const handleUpdate = async () => {
  updating.value = true;
  try {
    await systemAPI.update();
    ElMessage.success("更新任务已启动，请稍后刷新状态");
  } finally {
    updating.value = false;
  }
};

const handleRestart = async () => {
  await ElMessageBox.confirm("后端将立即重启，页面可能短暂不可用。确认继续？", "立即重启", {
    type: "warning",
  });
  restarting.value = true;
  try {
    await systemAPI.restart();
    ElMessage.success("重启已触发，请稍后刷新页面");
  } finally {
    restarting.value = false;
  }
};

onMounted(() => {
  notificationStore.startPolling();
  fetchVersion();
});

onUnmounted(() => {
  notificationStore.stopPolling();
});
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
}

.sidebar :deep(.el-menu) {
  flex: 1;
  border-right: none;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  border-bottom: 1px solid #434a50;
}

.logo h2 {
  font-size: 18px;
  font-weight: 600;
}

.version-entry {
  margin: auto 10px 8px;
  height: 34px;
  border: 2px solid rgba(255, 95, 95, 0.85);
  border-radius: 3px;
  color: #d7e3f1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.version-entry:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: #ff6b6b;
}

.version-text {
  font-size: 12px;
  font-weight: 600;
}

.version-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #67c23a;
}

.version-dot.warning {
  background: #e6a23c;
}

.version-dot.pending {
  background: #409eff;
}

.version-panel {
  text-align: center;
}

.version-number {
  font-size: 30px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 8px;
}

.version-state {
  color: #67c23a;
  font-size: 13px;
  margin-bottom: 14px;
}

.version-meta {
  color: #8a95a6;
  font-size: 12px;
  line-height: 22px;
}

.version-actions {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 18px;
}

.version-hint {
  color: #e6a23c;
  font-size: 12px;
  max-width: 180px;
  line-height: 18px;
}

.header {
  background: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.notification-badge {
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.username {
  font-size: 14px;
  color: #606266;
}

.main-content {
  background: #f5f5f5;
  padding: 20px;
}

.notification-header {
  padding: 0 0 10px 0;
  border-bottom: 1px solid #eee;
  margin-bottom: 10px;
}

.notification-list {
  padding: 10px;
}

.notification-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 15px;
  margin-bottom: 10px;
  background: #f5f5f5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.notification-item:hover {
  background: #e8e8e8;
}

.notification-item.unread {
  background: #e6f7ff;
  border-left: 3px solid #409eff;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-weight: 600;
  margin-bottom: 5px;
}

.notification-message {
  color: #666;
  font-size: 14px;
  margin-bottom: 5px;
}

.notification-time {
  color: #999;
  font-size: 12px;
}

.empty-notifications {
  padding: 50px 0;
}
</style>

