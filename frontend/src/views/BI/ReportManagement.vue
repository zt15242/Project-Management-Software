<template>
  <div class="report-management">
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="goToDesigner">创建报表</el-button>
    </div>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="8" v-for="report in reports" :key="report.id">
        <el-card class="report-card">
          <template #header>
            <div class="card-header">
              <span class="report-name">{{ report.name }}</span>
              <el-tag :type="getChartTypeColor(report.chart_type)">
                {{ getChartTypeLabel(report.chart_type) }}
              </el-tag>
            </div>
          </template>
          <div class="report-info">
            <div class="info-item">
              <span class="label">数据对象：</span>
              <span class="value">{{ report.object_name }}</span>
            </div>
            <div class="info-item">
              <span class="label">字段数：</span>
              <span class="value">{{ report.fields?.length || 0 }} 个</span>
            </div>
            <div class="report-desc">{{ report.description || '暂无描述' }}</div>
          </div>
          <template #footer>
            <div class="card-footer">
              <el-button size="small" @click="handleView(report)">预览数据</el-button>
              <el-button size="small" type="primary" @click="handleEdit(report)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(report)">删除</el-button>
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <!-- 查看报表对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      :title="currentReport?.name"
      width="1000px"
    >
      <div class="report-view">
        <div class="report-info-detail">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="数据源">{{ currentDatasourceName }}</el-descriptions-item>
            <el-descriptions-item label="数据对象">{{ currentReport?.object_name }}</el-descriptions-item>
            <el-descriptions-item label="图表类型">
              <el-tag :type="getChartTypeColor(currentReport?.chart_type)">
                {{ getChartTypeLabel(currentReport?.chart_type) }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
          
          <div style="margin-top: 15px;">
            <h4>X轴字段：</h4>
            <el-tag 
              v-for="field in currentReport?.chart_config?.xFields" 
              :key="field"
              style="margin-right: 8px;"
            >
              {{ field }}
            </el-tag>
            <el-text v-if="!currentReport?.chart_config?.xFields?.length" type="info">无</el-text>
          </div>
          
          <div style="margin-top: 10px;">
            <h4>Y轴字段：</h4>
            <el-tag 
              v-for="field in currentReport?.chart_config?.yFields" 
              :key="field"
              style="margin-right: 8px;"
            >
              {{ field }}
            </el-tag>
            <el-text v-if="!currentReport?.chart_config?.yFields?.length" type="info">无</el-text>
          </div>
          
          <div v-if="currentReport?.chart_config?.seriesFields?.length" style="margin-top: 10px;">
            <h4>分组字段：</h4>
            <el-tag 
              v-for="field in currentReport?.chart_config?.seriesFields" 
              :key="field"
              style="margin-right: 8px;"
            >
              {{ field }}
            </el-tag>
          </div>
        </div>
        
        <el-divider />
        
        <div class="preview-actions">
          <el-button type="primary" @click="loadReportPreview" :loading="executing">
            加载数据预览
          </el-button>
        </div>
        
        <div v-if="reportData && reportData.length > 0" class="data-preview">
          <el-alert 
            type="success" 
            :closable="false"
            :title="`共查询到 ${reportData.length} 条数据`"
            style="margin-bottom: 15px;"
          />
          
          <!-- 图表渲染区域 -->
          <div v-if="currentReport?.chart_type !== 'table'" class="chart-view">
            <div ref="chartContainer" style="width: 100%; height: 400px;"></div>
          </div>
          
          <!-- 表格显示 -->
          <el-table :data="reportData" border stripe max-height="400">
            <el-table-column 
              v-for="field in currentReport?.fields" 
              :key="field"
              :prop="field"
              :label="field"
              width="150"
              show-overflow-tooltip
            />
          </el-table>
        </div>
        
        <div v-else-if="reportData && reportData.length === 0" class="no-data">
          <el-empty description="暂无数据" />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { reportAPI, dataSourceAPI } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()

const props = defineProps({
  projectId: String
})

const reports = ref([])
const datasources = ref([])
const viewDialogVisible = ref(false)
const executing = ref(false)
const currentReport = ref(null)
const reportData = ref([])
const chartContainer = ref(null)
let chartInstance = null

const currentDatasourceName = computed(() => {
  if (!currentReport.value) return ''
  const ds = datasources.value.find(d => d.id === currentReport.value.datasource_id)
  return ds ? ds.name : '未知'
})

const getChartTypeLabel = (type) => {
  const labels = {
    line: '折线图',
    bar: '柱状图',
    pie: '饼图',
    table: '表格',
    area: '面积图',
    scatter: '散点图'
  }
  return labels[type] || type
}

const getChartTypeColor = (type) => {
  const colors = {
    line: 'primary',
    bar: 'success',
    pie: 'warning',
    table: 'info',
    area: 'primary',
    scatter: 'danger'
  }
  return colors[type] || ''
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

const fetchDataSources = async () => {
  if (!props.projectId) return
  
  try {
    const data = await dataSourceAPI.getDataSources({ project_id: props.projectId })
    datasources.value = data
  } catch (error) {
    ElMessage.error('获取数据源列表失败')
  }
}

const goToDesigner = () => {
  router.push({
    name: 'ReportDesigner',
    query: { project_id: props.projectId }
  })
}

const handleEdit = (report) => {
  router.push({
    name: 'ReportDesigner',
    query: { 
      project_id: props.projectId,
      report_id: report.id
    }
  })
}

const handleView = async (report) => {
  currentReport.value = report
  reportData.value = []
  viewDialogVisible.value = true
}

// 监听对话框关闭，清理图表实例
watch(viewDialogVisible, (newVal) => {
  if (!newVal && chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

const loadReportPreview = async () => {
  if (!currentReport.value) return
  
  executing.value = true
  try {
    const data = await dataSourceAPI.previewData(currentReport.value.datasource_id, {
      object_name: currentReport.value.object_name,
      fields: currentReport.value.fields,
      limit: 50
    })
    
    reportData.value = data.data || []
    
    if (reportData.value.length === 0) {
      ElMessage.info('暂无数据')
    } else {
      ElMessage.success(`加载成功，共 ${reportData.value.length} 条数据`)
      
      // 渲染图表
      await nextTick()
      renderChart()
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('数据加载失败')
  } finally {
    executing.value = false
  }
}

const renderChart = () => {
  if (!chartContainer.value || !currentReport.value || currentReport.value.chart_type === 'table') {
    return
  }
  
  // 销毁旧的图表实例
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  // 创建新的图表实例
  chartInstance = echarts.init(chartContainer.value)
  
  const config = currentReport.value.chart_config
  const chartType = currentReport.value.chart_type
  
  let option = {}
  
  if (chartType === 'line' || chartType === 'bar' || chartType === 'area') {
    // 折线图、柱状图、面积图
    const xFields = config.xFields || []
    const yFields = config.yFields || []
    
    // 按X轴字段分组统计
    const groupedData = {}
    reportData.value.forEach(item => {
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
        // 只有数值才能累加
        if (typeof value === 'number') {
          groupedData[xKey].values[yField].push(value)
        }
      })
    })
    
    const xData = Object.keys(groupedData)
    
    const series = yFields.map(field => {
      const data = xData.map(xKey => {
        const values = groupedData[xKey].values[field]
        // 如果有数值，计算平均值；否则使用计数
        if (values.length > 0) {
          return values.reduce((a, b) => a + b, 0) / values.length
        } else {
          // 对于非数值字段，使用记录数量
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
        text: currentReport.value.name,
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: yFields,
        top: 30
      },
      xAxis: {
        type: 'category',
        data: xData,
        axisLabel: {
          rotate: 30
        }
      },
      yAxis: {
        type: 'value'
      },
      series: series,
      grid: {
        bottom: 80
      }
    }
  } else if (chartType === 'pie') {
    // 饼图
    const xFields = config.xFields || []
    const yFields = config.yFields || []
    
    const pieData = reportData.value.map(item => ({
      name: xFields.map(field => item[field]).join('-'),
      value: yFields.length > 0 ? item[yFields[0]] : 1
    }))
    
    option = {
      title: {
        text: currentReport.value.name,
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        top: 50
      },
      series: [
        {
          name: currentReport.value.name,
          type: 'pie',
          radius: '50%',
          data: pieData,
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
    
    // 响应窗口大小变化
    window.addEventListener('resize', () => {
      if (chartInstance) {
        chartInstance.resize()
      }
    })
  }
}

const handleDelete = async (report) => {
  try {
    await ElMessageBox.confirm('确定要删除此报表吗？', '提示', {
      type: 'warning'
    })
    
    await reportAPI.deleteReport(report.id)
    ElMessage.success('删除成功')
    fetchReports()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

watch(() => props.projectId, () => {
  fetchReports()
  fetchDataSources()
}, { immediate: true })
</script>

<style scoped>
.report-management {
  padding: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-card {
  margin-bottom: 20px;
  transition: transform 0.3s, box-shadow 0.3s;
  height: 100%;
}

.report-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-name {
  font-weight: bold;
  font-size: 16px;
}

.report-info {
  padding: 10px 0;
}

.info-item {
  margin-bottom: 8px;
  font-size: 14px;
}

.info-item .label {
  color: #909399;
  margin-right: 5px;
}

.info-item .value {
  color: #303133;
  font-weight: 500;
}

.report-desc {
  color: #666;
  font-size: 13px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
  min-height: 30px;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.report-view {
  padding: 10px 0;
}

.report-info-detail h4 {
  margin: 10px 0 8px 0;
  font-size: 14px;
  color: #606266;
  font-weight: 600;
}

.preview-actions {
  text-align: center;
  margin: 20px 0;
}

.data-preview {
  margin-top: 20px;
}

.chart-view {
  margin-bottom: 20px;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.no-data {
  margin-top: 20px;
  padding: 40px;
  text-align: center;
}
</style>

