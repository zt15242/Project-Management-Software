import axios from './axios'

// 认证相关
export const authAPI = {
  login: (data) => axios.post('/auth/login', data),
  register: (data) => axios.post('/auth/register', data),
  getCurrentUser: () => axios.get('/auth/me')
}

// 用户相关
export const userAPI = {
  getUsers: () => axios.get('/users/'),
  getUser: (id) => axios.get(`/users/${id}`),
  updateUser: (id, data) => axios.put(`/users/${id}`, data),
  deleteUser: (id) => axios.delete(`/users/${id}`),
  changePassword: (data) => axios.post('/users/change-password', data),
  getUserStats: () => axios.get('/users/me/stats')
}

// 项目相关
export const projectAPI = {
  getProjects: (params) => axios.get('/projects/', { params }),
  getProject: (id) => axios.get(`/projects/${id}`),
  createProject: (data) => axios.post('/projects/', data),
  updateProject: (id, data) => axios.put(`/projects/${id}`, data),
  addMember: (projectId, userId) => axios.post(`/projects/${projectId}/members/${userId}`),
  removeMember: (projectId, userId) => axios.delete(`/projects/${projectId}/members/${userId}`)
}

// 任务相关
export const taskAPI = {
  getTasks: (params) => axios.get('/tasks/', { params }),
  getTask: (id) => axios.get(`/tasks/${id}`),
  createTask: (data) => axios.post('/tasks/', data),
  updateTask: (id, data) => axios.put(`/tasks/${id}`, data),
  deleteTask: (id) => axios.delete(`/tasks/${id}`)
}

// 课题相关
export const topicAPI = {
  getTopics: (params) => axios.get('/topics/', { params }),
  getTopic: (id) => axios.get(`/topics/${id}`),
  createTopic: (data) => axios.post('/topics/', data),
  updateTopic: (id, data) => axios.put(`/topics/${id}`, data),
  deleteTopic: (id) => axios.delete(`/topics/${id}`),
  uploadAttachment: (id, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return axios.post(`/topics/${id}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  startRetest: (id) => axios.post(`/topics/${id}/retest`),
  closeTopic: (id) => axios.post(`/topics/${id}/close`),
  reopenTopic: (id) => axios.post(`/topics/${id}/reopen`),
  // 评论相关
  getComments: (id) => axios.get(`/topics/${id}/comments`),
  addComment: (id, data) => axios.post(`/topics/${id}/comments`, data)
}

// 统计相关
export const statisticsAPI = {
  getProjectStatistics: (projectId) => axios.get(`/statistics/projects/${projectId}`),
  getAllStatistics: () => axios.get('/statistics/overview')
}

// 通知相关
export const notificationAPI = {
  getNotifications: (params) => axios.get('/notifications/', { params }),
  getUnreadCount: () => axios.get('/notifications/unread/count'),
  markAsRead: (id) => axios.put(`/notifications/${id}/read`),
  markAllAsRead: () => axios.put('/notifications/read-all'),
  deleteNotification: (id) => axios.delete(`/notifications/${id}`)
}

// BI配置相关
export const biConfigAPI = {
  getEnabledDataSourceTypes: () => axios.get('/bi/config/datasource-types')
}

// BI数据源相关
export const dataSourceAPI = {
  getDataSources: (params) => axios.get('/bi/datasources', { params }),
  getDataSource: (id) => axios.get(`/bi/datasources/${id}`),
  createDataSource: (data) => axios.post('/bi/datasources', data),
  updateDataSource: (id, data) => axios.put(`/bi/datasources/${id}`, data),
  deleteDataSource: (id) => axios.delete(`/bi/datasources/${id}`),
  getObjects: (id) => axios.get(`/bi/datasources/${id}/objects`),
  previewData: (id, data) => axios.post(`/bi/datasources/${id}/preview`, data)
}

// BI报表相关
export const reportAPI = {
  getReports: (params) => axios.get('/bi/reports', { params }),
  getReport: (id) => axios.get(`/bi/reports/${id}`),
  createReport: (data) => axios.post('/bi/reports', data),
  updateReport: (id, data) => axios.put(`/bi/reports/${id}`, data),
  deleteReport: (id) => axios.delete(`/bi/reports/${id}`),
  executeReport: (id) => axios.post(`/bi/reports/${id}/execute`)
}

// BI仪表板相关
export const dashboardAPI = {
  getDashboards: (params) => axios.get('/bi/dashboards', { params }),
  getDashboard: (id) => axios.get(`/bi/dashboards/${id}`),
  createDashboard: (data) => axios.post('/bi/dashboards', data),
  updateDashboard: (id, data) => axios.put(`/bi/dashboards/${id}`, data),
  deleteDashboard: (id) => axios.delete(`/bi/dashboards/${id}`)
}

// 代码发布相关
export const deploymentAPI = {
  // 发布申请（包）管理
  getDeployments: (params) => axios.get('/deployments/', { params }),
  getDeployment: (id) => axios.get(`/deployments/${id}`),
  createDeployment: (data) => {
    const formData = new FormData()
    formData.append('title', data.title)
    formData.append('project_id', data.project_id)
    formData.append('deployment_type', data.deployment_type)
    if (data.description) formData.append('description', data.description)
    if (data.environment_id) formData.append('environment_id', data.environment_id)
    if (data.package_path) formData.append('package_path', data.package_path)
    if (data.remote_package_id) formData.append('remote_package_id', data.remote_package_id)
    return axios.post('/deployments/', formData)
  },
  updateDeployment: (id, data) => axios.put(`/deployments/${id}`, data),
  deleteDeployment: (id) => axios.delete(`/deployments/${id}`),

  // 版本管理
  uploadVersion: (deploymentId, data) => {
    const formData = new FormData()
    if (data.description) formData.append('description', data.description)
    if (data.file) formData.append('file', data.file)
    return axios.post(`/deployments/${deploymentId}/versions`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  getVersion: (deploymentId, version) => axios.get(`/deployments/${deploymentId}/versions/${version}`),
  deleteVersion: (deploymentId, version) => axios.delete(`/deployments/${deploymentId}/versions/${version}`),

  // 版本审核和部署
  reviewVersion: (deploymentId, version, data) => {
    const formData = new FormData()
    formData.append('action', data.action)
    if (data.comment) formData.append('comment', data.comment)
    return axios.post(`/deployments/${deploymentId}/versions/${version}/review`, formData)
  },
  deployVersion: (deploymentId, version) => axios.post(`/deployments/${deploymentId}/versions/${version}/deploy`),
  reanalyzeVersion: (deploymentId, version) => axios.post(`/deployments/${deploymentId}/versions/${version}/reanalyze`),

  // 版本对比
  compareVersions: (deploymentId, version1, version2) => axios.get(`/deployments/${deploymentId}/versions/${version1}/compare/${version2}`),

  // 远程包管理
  getRemotePackages: (environmentId) => axios.get(`/deployments/remote-packages/${environmentId}`),
  matchOrCreatePackage: (environmentId, data) => {
    const formData = new FormData()
    formData.append('package_path', data.package_path)
    formData.append('package_name', data.package_name)
    return axios.post(`/deployments/match-or-create-package/${environmentId}`, formData)
  },

  // 文件查看
  getVersionFiles: (deploymentId, version) => axios.get(`/deployments/${deploymentId}/versions/${version}/files`),
  getVersionFileContent: (deploymentId, version, path) => axios.get(`/deployments/${deploymentId}/versions/${version}/files/content`, { params: { path } })
}

// AI配置相关
export const aiConfigAPI = {
  getConfigs: () => axios.get('/ai-config/'),
  getConfig: (id) => axios.get(`/ai-config/${id}`),
  getActiveConfig: () => axios.get('/ai-config/active'),
  createConfig: (data) => axios.post('/ai-config/', data),
  updateConfig: (id, data) => axios.put(`/ai-config/${id}`, data),
  deleteConfig: (id) => axios.delete(`/ai-config/${id}`),
  testConfig: (id) => axios.post(`/ai-config/${id}/test`)
}

// 环境配置相关
export const environmentAPI = {
  getProjectEnvironments: (projectId) => axios.get(`/environments/project/${projectId}`),
  createEnvironment: (projectId, data) => axios.post(`/environments/?project_id=${projectId}`, data),
  updateEnvironment: (id, data) => axios.put(`/environments/${id}`, data),
  deleteEnvironment: (id) => axios.delete(`/environments/${id}`),
  loginEnvironment: (id, forceRefresh = false) => axios.post(
    `/environments/${id}/login?force_refresh=${forceRefresh}`,
    {},
    { timeout: 120000 } // 增加超时时间到120秒（2分钟）
  ),
  getCookies: (id) => axios.get(`/environments/${id}/cookies`)
}

// 日报相关
export const dailyReportAPI = {
  getDailyReports: (params) => axios.get('/daily-reports/', { params }),
  getDailyReport: (id) => axios.get(`/daily-reports/${id}`),
  createDailyReport: (data) => axios.post('/daily-reports/', data),
  updateDailyReport: (id, data) => axios.put(`/daily-reports/${id}`, data),
  deleteDailyReport: (id) => axios.delete(`/daily-reports/${id}`)
}

// 邮件配置相关
export const emailConfigAPI = {
  getConfig: () => axios.get('/email-config'),
  saveConfig: (data) => axios.post('/email-config', data),
  testConfig: (params) => axios.post('/email-config/test', null, { params }),
  getStatus: () => axios.get('/email-config/status'),
  sendCode: (data) => axios.post('/email-config/send-code', data)
}
