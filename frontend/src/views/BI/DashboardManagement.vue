<template>
  <div class="dashboard-management">
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="showCreateDialog">创建仪表板</el-button>
    </div>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12" v-for="dashboard in dashboards" :key="dashboard.id">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span class="dashboard-name">{{ dashboard.name }}</span>
              <el-tag type="primary">{{ dashboard.report_ids.length }} 个报表</el-tag>
            </div>
          </template>
          <div class="dashboard-desc">{{ dashboard.description || '暂无描述' }}</div>
          <template #footer>
            <div class="card-footer">
              <el-button size="small" @click="handleView(dashboard)">查看</el-button>
              <el-button size="small" type="primary" @click="handleEdit(dashboard)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(dashboard)">删除</el-button>
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建/编辑仪表板对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
    >
      <el-form :model="dashboardForm" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="仪表板名称" prop="name">
          <el-input v-model="dashboardForm.name" placeholder="请输入仪表板名称" />
        </el-form-item>
        <el-form-item label="选择报表" prop="report_ids">
          <el-select 
            v-model="dashboardForm.report_ids" 
            multiple 
            placeholder="选择要添加的报表" 
            style="width: 100%"
          >
            <el-option
              v-for="report in reports"
              :key="report.id"
              :label="report.name"
              :value="report.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="布局配置">
          <el-input 
            v-model="layoutConfigStr" 
            type="textarea" 
            :rows="6" 
            placeholder='{"columns": 2, "height": 300}'
          />
          <div class="form-tip">配置仪表板的布局参数（JSON格式）</div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="dashboardForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 查看仪表板对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      :title="currentDashboard?.name"
      width="1400px"
      fullscreen
    >
      <div class="dashboard-view" v-loading="loadingReports">
        <div class="dashboard-grid">
          <el-card 
            v-for="reportId in currentDashboard?.report_ids" 
            :key="reportId"
            class="report-widget"
          >
            <template #header>
              <div class="widget-header">
                <div>
                  <span class="widget-title">{{ getReportName(reportId) }}</span>
                  <el-tag 
                    v-if="getReport(reportId)" 
                    :type="getChartTypeColor(getReport(reportId).chart_type)"
                    size="small"
                    style="margin-left: 10px;"
                  >
                    {{ getChartTypeLabel(getReport(reportId).chart_type) }}
                  </el-tag>
                </div>
              </div>
            </template>
            <div class="widget-content">
              <div 
                v-if="reportDataMap[reportId] && reportDataMap[reportId].length > 0" 
                class="widget-data"
              >
                <!-- 图表区域 -->
                <div 
                  v-if="getReport(reportId)?.chart_type !== 'table'"
                  :ref="el => { if (el) chartRefs[reportId] = el }"
                  class="widget-chart"
                ></div>
              </div>
              <div v-else class="widget-placeholder">
                <el-empty description="暂无数据" />
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed, nextTick, onBeforeUnmount } from 'vue'
import { dashboardAPI, reportAPI, dataSourceAPI } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const props = defineProps({
  projectId: String
})

const dashboards = ref([])
const reports = ref([])
const dialogVisible = ref(false)
const viewDialogVisible = ref(false)
const formRef = ref()
const submitting = ref(false)
const isEdit = ref(false)
const currentDashboard = ref(null)
const layoutConfigStr = ref('{}')
const reportDataMap = ref({})
const loadingReports = ref(false)
const chartInstances = ref({})
const chartRefs = ref({})

const dashboardForm = reactive({
  name: '',
  report_ids: [],
  layout: {},
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入仪表板名称', trigger: 'blur' }],
  report_ids: [{ required: true, message: '请选择至少一个报表', trigger: 'change' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑仪表板' : '创建仪表板')

const fetchDashboards = async () => {
  if (!props.projectId) return
  
  try {
    const data = await dashboardAPI.getDashboards({ project_id: props.projectId })
    dashboards.value = data
  } catch (error) {
    ElMessage.error('获取仪表板列表失败')
  }
}

const fetchReports = async () => {
  if (!props.projectId) return
  
  try {
    const data = await reportAPI.getReports({ project_id: props.projectId })
    reports.value = data
  } catch (error) {
    ElMessage.error('获取报表列表失败')
  }
}

const getReportName = (reportId) => {
  const report = reports.value.find(r => r.id === reportId)
  return report ? report.name : '未知报表'
}

const getReport = (reportId) => {
  return reports.value.find(r => r.id === reportId)
}

const getChartTypeLabel = (type) => {
  const labels = {
    line: '折线图',
    bar: '柱状图',
    pie: '饼图',
    table: '表格',
    area: '面积图'
  }
  return labels[type] || type
}

const getChartTypeColor = (type) => {
  const colors = {
    line: 'primary',
    bar: 'success',
    pie: 'warning',
    table: 'info',
    area: 'primary'
  }
  return colors[type] || ''
}

const showCreateDialog = () => {
  isEdit.value = false
  Object.assign(dashboardForm, {
    name: '',
    report_ids: [],
    layout: {},
    description: ''
  })
  layoutConfigStr.value = '{}'
  dialogVisible.value = true
}

const handleEdit = (dashboard) => {
  isEdit.value = true
  currentDashboard.value = dashboard
  Object.assign(dashboardForm, {
    name: dashboard.name,
    report_ids: dashboard.report_ids,
    layout: dashboard.layout,
    description: dashboard.description
  })
  layoutConfigStr.value = JSON.stringify(dashboard.layout, null, 2)
  dialogVisible.value = true
}

const handleView = async (dashboard) => {
  currentDashboard.value = dashboard
  reportDataMap.value = {}
  chartRefs.value = {}
  viewDialogVisible.value = true
  
  // 自动加载所有报表数据
  await loadAllReportsData()
}

const loadAllReportsData = async () => {
  if (!currentDashboard.value) return
  
  loadingReports.value = true
  try {
    const reportIds = currentDashboard.value.report_ids || []
    
    for (const reportId of reportIds) {
      const report = reports.value.find(r => r.id === reportId)
      if (report) {
        try {
          const data = await dataSourceAPI.previewData(report.datasource_id, {
            object_name: report.object_name,
            fields: report.fields,
            limit: 100
          })
          reportDataMap.value[reportId] = data.data || []
        } catch (error) {
          console.error(`加载报表 ${report.name} 失败:`, error)
        }
      }
    }
    
    // 渲染所有图表
    await nextTick()
    renderAllCharts()
    
  } catch (error) {
    console.error('加载仪表板数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loadingReports.value = false
  }
}

const renderAllCharts = () => {
  if (!currentDashboard.value) return
  
  const reportIds = currentDashboard.value.report_ids || []
  
  reportIds.forEach(reportId => {
    const report = getReport(reportId)
    const reportData = reportDataMap.value[reportId]
    
    if (report && reportData && reportData.length > 0 && report.chart_type !== 'table') {
      renderChart(reportId, report, reportData)
    }
  })
}

const renderChart = (reportId, report, reportData) => {
  const container = chartRefs.value[reportId]
  if (!container) return
  
  // 销毁旧的图表实例
  if (chartInstances.value[reportId]) {
    chartInstances.value[reportId].dispose()
  }
  
  // 创建新的图表实例
  const chartInstance = echarts.init(container)
  chartInstances.value[reportId] = chartInstance
  
  const config = report.chart_config
  const chartType = report.chart_type
  
  let option = {}
  
  if (chartType === 'line' || chartType === 'bar' || chartType === 'area') {
    const xFields = config.xFields || []
    const yFields = config.yFields || []
    
    // 按X轴字段分组统计
    const groupedData = {}
    reportData.forEach(item => {
      const xKey = xFields.map(field => item[field]).join('-')
      if (!groupedData[xKey]) {
        groupedData[xKey] = { count: 0, values: {} }
        yFields.forEach(yField => {
          groupedData[xKey].values[yField] = []
        })
      }
      groupedData[xKey].count++
      
      yFields.forEach(yField => {
        const value = item[yField]
        if (typeof value === 'number') {
          groupedData[xKey].values[yField].push(value)
        }
      })
    })
    
    const xData = Object.keys(groupedData)
    
    const series = yFields.map(field => {
      const data = xData.map(xKey => {
        const values = groupedData[xKey].values[field]
        if (values.length > 0) {
          return values.reduce((a, b) => a + b, 0) / values.length
        } else {
          return groupedData[xKey].count
        }
      })
      
      return {
        name: field,
        type: chartType === 'area' ? 'line' : chartType,
        data: data,
        areaStyle: chartType === 'area' ? {} : undefined,
        smooth: chartType === 'line' || chartType === 'area'
      }
    })
    
    option = {
      title: {
        text: report.name,
        left: 'center',
        textStyle: {
          fontSize: 14
        }
      },
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: yFields,
        top: 30,
        textStyle: {
          fontSize: 12
        }
      },
      xAxis: {
        type: 'category',
        data: xData,
        axisLabel: {
          rotate: 30,
          fontSize: 11
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          fontSize: 11
        }
      },
      series: series,
      grid: {
        bottom: 60,
        left: 50,
        right: 30,
        top: 80
      }
    }
  } else if (chartType === 'pie') {
    const xFields = config.xFields || []
    const yFields = config.yFields || []
    
    const pieData = reportData.map(item => ({
      name: xFields.map(field => item[field]).join('-'),
      value: yFields.length > 0 ? item[yFields[0]] : 1
    }))
    
    option = {
      title: {
        text: report.name,
        left: 'center',
        textStyle: {
          fontSize: 14
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        top: 40,
        textStyle: {
          fontSize: 11
        }
      },
      series: [
        {
          name: report.name,
          type: 'pie',
          radius: '50%',
          data: pieData,
          label: {
            fontSize: 11
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
  }
  
  if (option && Object.keys(option).length > 0) {
    chartInstance.setOption(option)
  }
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate()
  if (!valid) return
  
  // 解析布局配置
  try {
    dashboardForm.layout = JSON.parse(layoutConfigStr.value)
  } catch (e) {
    ElMessage.error('布局配置格式错误，请输入有效的JSON')
    return
  }
  
  submitting.value = true
  try {
    const data = {
      ...dashboardForm,
      project_id: props.projectId
    }
    
    if (isEdit.value) {
      await dashboardAPI.updateDashboard(currentDashboard.value.id, data)
      ElMessage.success('仪表板更新成功')
    } else {
      await dashboardAPI.createDashboard(data)
      ElMessage.success('仪表板创建成功')
    }
    
    dialogVisible.value = false
    fetchDashboards()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (dashboard) => {
  try {
    await ElMessageBox.confirm('确定要删除此仪表板吗？', '提示', {
      type: 'warning'
    })
    
    await dashboardAPI.deleteDashboard(dashboard.id)
    ElMessage.success('删除成功')
    fetchDashboards()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 监听对话框关闭，清理图表实例
watch(viewDialogVisible, (newVal) => {
  if (!newVal) {
    Object.values(chartInstances.value).forEach(instance => {
      if (instance) {
        instance.dispose()
      }
    })
    chartInstances.value = {}
  }
})

// 组件卸载时清理
onBeforeUnmount(() => {
  Object.values(chartInstances.value).forEach(instance => {
    if (instance) {
      instance.dispose()
    }
  })
})

watch(() => props.projectId, () => {
  fetchDashboards()
  fetchReports()
}, { immediate: true })
</script>

<style scoped>
.dashboard-management {
  padding: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.dashboard-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-name {
  font-weight: bold;
  font-size: 16px;
}

.dashboard-desc {
  color: #666;
  min-height: 40px;
  margin: 10px 0;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.dashboard-view {
  padding: 20px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.report-widget {
  min-height: 300px;
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.widget-title {
  font-weight: 600;
  font-size: 14px;
}

.widget-content {
  min-height: 350px;
  padding: 10px;
}

.widget-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 350px;
}

.widget-data {
  width: 100%;
  height: 100%;
}

.widget-chart {
  width: 100%;
  height: 350px;
}
</style>

