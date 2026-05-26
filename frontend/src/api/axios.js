import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const instance = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
instance.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
instance.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', error)

    if (error.response) {
      // 优先显示后端返回的详细错误信息
      const errorMessage = error.response.data?.detail || error.response.data?.message || error.message
      const currentPath = window.location.pathname

      switch (error.response.status) {
        case 401:
          // 检查是否是远程API的cookie过期错误
          const isRemoteCookieError = errorMessage?.includes('Cookie已过期') ||
            errorMessage?.includes('环境未登录') ||
            errorMessage?.includes('请重新登录环境')

          // 如果是登录接口返回401，直接显示后端的错误信息（用户名或密码错误）
          if (error.config.url?.includes('/auth/login')) {
            ElMessage.error(errorMessage)
          }
          // 如果是远程API的cookie过期，只显示错误信息，不退出登录
          else if (isRemoteCookieError) {
            ElMessage.error(errorMessage)
          }
          // 其他情况说明本系统token失效，需要重新登录
          else {
            ElMessage.error('登录已过期，请重新登录')
            localStorage.removeItem('token')
            // 只有不在登录页时才跳转
            if (currentPath !== '/login') {
              router.push('/login')
            }
          }
          break
        case 403:
          ElMessage.error(errorMessage || '没有权限访问')
          break
        case 404:
          ElMessage.error(errorMessage || '请求的资源不存在')
          break
        case 500:
          ElMessage.error(`服务器错误: ${errorMessage}`)
          console.error('Server Error Details:', error.response.data)
          break
        default:
          ElMessage.error(errorMessage || '请求失败')
      }
    } else if (error.request) {
      ElMessage.error('无法连接到服务器，请检查后端是否启动')
      console.error('No response received:', error.request)
    } else {
      ElMessage.error('网络错误，请检查您的网络连接')
      console.error('Request error:', error.message)
    }
    return Promise.reject(error)
  }
)

export default instance

