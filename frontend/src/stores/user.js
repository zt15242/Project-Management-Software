import { defineStore } from 'pinia'
import { authAPI } from '@/api'
import router from '@/router'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
    isExternal: (state) => state.user?.role === 'external_personnel',
    role: (state) => state.user?.role,
    userId: (state) => state.user?.id
  },

  actions: {
    async login(credentials) {
      try {
        console.log('开始登录...')
        const response = await authAPI.login(credentials)
        console.log('登录响应:', response)
        this.token = response.access_token
        localStorage.setItem('token', response.access_token)
        console.log('Token已保存')

        await this.getCurrentUser()
        console.log('用户信息已获取:', this.user)

        ElMessage.success('登录成功')
        console.log('准备跳转到首页...')
        await router.push('/')
        console.log('跳转完成')
      } catch (error) {
        console.error('登录错误:', error)
        ElMessage.error('登录失败')
        throw error
      }
    },

    async register(userData) {
      try {
        console.log('注册数据:', userData)
        const response = await authAPI.register(userData)
        console.log('注册响应:', response)
        ElMessage.success('注册成功，请登录')
        router.push('/login')
      } catch (error) {
        console.error('注册错误:', error)
        // 错误已经在 axios 拦截器中处理了，这里不再重复显示
        throw error
      }
    },

    async getCurrentUser() {
      try {
        console.log('开始获取当前用户信息...')
        const user = await authAPI.getCurrentUser()
        console.log('获取到用户:', user)
        this.user = user
        console.log('用户信息已设置到 store')
      } catch (error) {
        console.error('获取用户信息失败:', error)
        // 不要在这里 logout，因为可能只是获取信息失败
        throw error
      }
    },

    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('token')
      ElMessage.info('已退出登录')
      router.push('/login')
    }
  }
})

