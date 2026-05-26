import { defineStore } from 'pinia'
import { notificationAPI } from '@/api'
import { ElNotification } from 'element-plus'

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    notifications: [],
    unreadCount: 0,
    pollingInterval: null
  }),
  
  actions: {
    async fetchNotifications(unreadOnly = false) {
      try {
        this.notifications = await notificationAPI.getNotifications({ unread_only: unreadOnly })
      } catch (error) {
        console.error('获取通知失败', error)
      }
    },
    
    async fetchUnreadCount() {
      try {
        const response = await notificationAPI.getUnreadCount()
        const newCount = response.count
        
        // 如果有新通知，显示系统通知
        if (newCount > this.unreadCount && this.unreadCount > 0) {
          this.showSystemNotification()
        }
        
        this.unreadCount = newCount
      } catch (error) {
        console.error('获取未读数量失败', error)
      }
    },
    
    async markAsRead(notificationId) {
      try {
        await notificationAPI.markAsRead(notificationId)
        await this.fetchNotifications()
        await this.fetchUnreadCount()
      } catch (error) {
        console.error('标记已读失败', error)
      }
    },
    
    async markAllAsRead() {
      try {
        await notificationAPI.markAllAsRead()
        await this.fetchNotifications()
        await this.fetchUnreadCount()
      } catch (error) {
        console.error('标记全部已读失败', error)
      }
    },
    
    async deleteNotification(notificationId) {
      try {
        await notificationAPI.deleteNotification(notificationId)
        await this.fetchNotifications()
        await this.fetchUnreadCount()
      } catch (error) {
        console.error('删除通知失败', error)
      }
    },
    
    showSystemNotification() {
      // 检查浏览器是否支持通知
      if (!('Notification' in window)) {
        console.log('浏览器不支持通知')
        return
      }
      
      // 请求通知权限
      if (Notification.permission === 'granted') {
        this.createNotification()
      } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
          if (permission === 'granted') {
            this.createNotification()
          }
        })
      }
    },
    
    createNotification() {
      const notification = new Notification('项目管理系统', {
        body: '您有新的通知',
        icon: '/vite.svg',
        badge: '/vite.svg'
      })
      
      notification.onclick = () => {
        window.focus()
        notification.close()
      }
      
      // 同时显示Element Plus通知
      ElNotification({
        title: '新通知',
        message: '您有新的消息',
        type: 'info',
        duration: 3000
      })
    },
    
    startPolling() {
      // 立即获取一次
      this.fetchUnreadCount()
      
      // 每3秒轮询一次（实时性更好）
      this.pollingInterval = setInterval(() => {
        this.fetchUnreadCount()
      }, 3000)
    },
    
    stopPolling() {
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval)
        this.pollingInterval = null
      }
    }
  }
})

