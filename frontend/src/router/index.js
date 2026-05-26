import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue')
      },
      {
        path: 'projects',
        name: 'Projects',
        component: () => import('@/views/Projects.vue')
      },
      {
        path: 'projects/:id',
        name: 'ProjectDetail',
        component: () => import('@/views/ProjectDetail.vue')
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('@/views/Tasks.vue')
      },
      {
        path: 'topics',
        name: 'Topics',
        component: () => import('@/views/Topics.vue')
      },
      {
        path: 'topics/:id',
        name: 'TopicDetail',
        component: () => import('@/views/TopicDetail.vue')
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue')
      },
      {
        path: 'notifications',
        name: 'Notifications',
        component: () => import('@/views/Notifications.vue')
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue')
      },
      {
        path: 'bi',
        name: 'BI',
        component: () => import('@/views/BI/index.vue')
      },
      {
        path: 'bi/report-designer',
        name: 'ReportDesigner',
        component: () => import('@/views/BI/ReportDesigner.vue')
      },
      {
        path: 'deployments',
        name: 'Deployments',
        component: () => import('@/views/Deployments.vue')
      },
      {
        path: 'deployments/:id',
        name: 'DeploymentDetail',
        component: () => import('@/views/DeploymentDetail.vue')
      },
      {
        path: 'ai-config',
        name: 'AIConfig',
        component: () => import('@/views/AIConfig.vue'),
        meta: { requiresAdmin: true }
      },
      {
        path: 'asr-config',
        name: 'ASRConfig',
        component: () => import('@/views/ASRConfig.vue'),
        meta: { requiresAdmin: true, title: '语音识别配置' }
      },
      {
        path: 'daily-report',
        name: 'DailyReport',
        component: () => import('@/views/DailyReport.vue')
      },
      {
        path: 'background-tasks',
        name: 'BackgroundTasks',
        component: () => import('@/views/BackgroundTasks.vue'),
        meta: { title: '后台任务' }
      },
      {
        path: 'email-config',
        name: 'EmailConfig',
        component: () => import('@/views/EmailConfig.vue'),
        meta: { requiresAdmin: true, title: '邮局配置' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }

  if ((to.path === '/login' || to.path === '/register') && token) {
    return next('/')
  }

  // 如果已登录但没有用户信息，尝试获取
  if (token && !userStore.user) {
    try {
      await userStore.getCurrentUser()
    } catch (err) {
      // 获取用户信息失败，可能 token 已过期
      localStorage.removeItem('token')
      return next('/login')
    }
  }

  // 权限控制
  if (userStore.isLoggedIn && userStore.user) {
    const isExternal = userStore.user.role === 'external_personnel'

    // 如果是外来人员且尝试访问除topics、profile、notifications以外的页面，重定向到topics
    const allowedPaths = ['/topics', '/profile', '/notifications', '/login', '/register']
    const isAllowed = allowedPaths.some(path => to.path.startsWith(path))

    if (isExternal && !isAllowed) {
      // 如果访问首页，直接去课题
      if (to.path === '/' || to.path === '/dashboard' || to.path === '/projects') {
        return next('/topics')
      } else {
        // 其他页面禁止访问
        return next('/topics')
      }
    }
  }

  next()
})

export default router
