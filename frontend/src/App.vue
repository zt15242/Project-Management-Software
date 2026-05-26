<template>
  <router-view />
</template>

<script setup>
import { onMounted } from "vue";
import { useUserStore } from "@/stores/user";
import { useNotificationStore } from "@/stores/notification";

const userStore = useUserStore();
const notificationStore = useNotificationStore();

onMounted(() => {
  // 检查是否有保存的登录状态
  const token = localStorage.getItem("token");
  if (token && !userStore.user) {
    userStore.getCurrentUser();
    notificationStore.startPolling();
  }
});
</script>

<style scoped>
/* App级别样式 */
</style>

