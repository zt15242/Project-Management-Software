<template>
  <div class="report-designer">
    <el-container>
      <!-- 左侧：数据对象和字段列表 -->
      <el-aside width="300px" class="designer-aside">
        <div class="aside-header">
          <h3>数据源对象</h3>
        </div>
        
        <el-select 
          v-model="selectedDataSourceId" 
          placeholder="选择数据源"
          style="width: 100%; margin-bottom: 15px;"
          @change="loadObjects"
        >
          <el-option
            v-for="ds in datasources"
            :key="ds.id"
            :label="ds.name"
            :value="ds.id"
          />
        </el-select>

        <el-collapse v-model="activeObjects" accordion>
          <el-collapse-item 
            v-for="obj in objects" 
            :key="obj.name"
            :title="obj.name"
            :name="obj.name"
          >
            <div class="field-list">
              <div 
                v-for="field in obj.fields"
                :key="field.name"
                class="field-item"
                draggable="true"
                @dragstart="handleFieldDragStart($event, field, obj.name)"
              >
                <el-icon><Grid /></el-icon>
                <span>{{ field.label }}</span>
                <el-tag size="small" type="info">{{ field.type }}</el-tag>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-aside>

      <!-- 中间：报表设计区 -->
      <el-container>
        <el-header height="60px" class="designer-header">
          <div class="header-left">
            <el-tag v-if="isEditMode" type="warning" style="margin-right: 10px;">编辑模式</el-tag>
            <el-tag v-else type="success" style="margin-right: 10px;">创建模式</el-tag>
            <el-input 
              v-model="reportConfig.name" 
              placeholder="输入报表名称"
              style="width: 300px;"
            />
          </div>
          <div>
            <el-button @click="handleCancel">取消</el-button>
            <el-button type="primary" @click="handleSave" :loading="saving">
              {{ isEditMode ? '更新报表' : '保存报表' }}
            </el-button>
          </div>
        </el-header>

        <el-main class="designer-main">
          <!-- 图表类型选择 -->
          <div class="chart-type-selector">
            <h4>图表类型</h4>
            <el-radio-group v-model="reportConfig.chart_type">
              <el-radio-button value="line">折线图</el-radio-button>
              <el-radio-button value="bar">柱状图</el-radio-button>
              <el-radio-button value="pie">饼图</el-radio-button>
              <el-radio-button value="table">表格</el-radio-button>
              <el-radio-button value="area">面积图</el-radio-button>
            </el-radio-group>
          </div>

          <!-- 字段配置区 -->
          <div class="field-config-area">
            <!-- X轴（维度） -->
            <div class="config-section">
              <div class="section-header">
                <h4>X轴 / 维度</h4>
                <el-tag size="small">可拖拽多个字段</el-tag>
              </div>
              <div 
                class="drop-zone"
                @drop="handleDrop($event, 'xFields')"
                @dragover.prevent
                @dragenter.prevent
              >
                <div v-if="reportConfig.chart_config.xFields.length > 0" class="field-chips">
                  <div v-for="(field, index) in reportConfig.chart_config.xFields" :key="index" class="field-chip">
                    {{ field }}
                    <el-icon @click="removeFieldFromArray('xFields', index)"><Close /></el-icon>
                  </div>
                </div>
                <div v-else class="drop-placeholder">
                  拖拽字段到这里（支持多个）
                </div>
              </div>
            </div>

            <!-- Y轴（度量） -->
            <div class="config-section">
              <div class="section-header">
                <h4>Y轴 / 度量</h4>
                <el-tag size="small">可拖拽多个字段</el-tag>
              </div>
              <div 
                class="drop-zone"
                @drop="handleDrop($event, 'yFields')"
                @dragover.prevent
                @dragenter.prevent
              >
                <div v-if="reportConfig.chart_config.yFields.length > 0" class="field-chips">
                  <div v-for="(field, index) in reportConfig.chart_config.yFields" :key="index" class="field-chip">
                    {{ field }}
                    <el-icon @click="removeFieldFromArray('yFields', index)"><Close /></el-icon>
                  </div>
                </div>
                <div v-else class="drop-placeholder">
                  拖拽字段到这里（支持多个）
                </div>
              </div>
            </div>

            <!-- 分组字段 -->
            <div class="config-section" v-if="['line', 'bar', 'area'].includes(reportConfig.chart_type)">
              <div class="section-header">
                <h4>分组字段（可选）</h4>
                <el-tag size="small">可拖拽多个字段</el-tag>
              </div>
              <div 
                class="drop-zone"
                @drop="handleDrop($event, 'seriesFields')"
                @dragover.prevent
                @dragenter.prevent
              >
                <div v-if="reportConfig.chart_config.seriesFields.length > 0" class="field-chips">
                  <div v-for="(field, index) in reportConfig.chart_config.seriesFields" :key="index" class="field-chip">
                    {{ field }}
                    <el-icon @click="removeFieldFromArray('seriesFields', index)"><Close /></el-icon>
                  </div>
                </div>
                <div v-else class="drop-placeholder">
                  拖拽字段到这里（支持多个）
                </div>
              </div>
            </div>

            <!-- 已选字段列表 -->
            <div class="config-section">
              <div class="section-header">
                <h4>已选字段</h4>
                <el-button 
                  v-if="reportConfig.fields.length > 0"
                  size="small" 
                  type="danger" 
                  text
                  @click="clearAllFields"
                >
                  清空所有字段
                </el-button>
              </div>
              <div v-if="reportConfig.object_name" style="margin-bottom: 10px;">
                <el-tag type="info" size="small">
                  当前对象：{{ reportConfig.object_name }}
                </el-tag>
              </div>
              <el-tag 
                v-for="field in reportConfig.fields"
                :key="field"
                closable
                @close="removeFromFields(field)"
                style="margin-right: 8px; margin-bottom: 8px;"
              >
                {{ field }}
              </el-tag>
              <el-text v-if="reportConfig.fields.length === 0" type="info">
                暂无字段，请从左侧拖拽字段
              </el-text>
            </div>
          </div>

          <!-- 预览区 -->
          <div class="preview-section">
            <div class="preview-header">
              <h4>数据预览</h4>
              <el-button 
                type="primary" 
                size="small" 
                @click="loadPreviewData"
                :loading="loadingPreview"
                :disabled="!canPreview"
              >
                刷新预览
              </el-button>
            </div>
            <div class="preview-container">
              <div v-if="!canPreview" class="preview-empty">
                <el-empty description="请先配置X轴和Y轴字段" />
              </div>
              
              <div v-else-if="loadingPreview" class="preview-loading">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>加载数据中...</span>
              </div>
              
              <div v-else-if="previewData.length > 0" class="preview-content">
                <el-alert 
                  type="success" 
                  :closable="false"
                  :title="`共查询到 ${previewData.length} 条数据`"
                  style="margin-bottom: 15px;"
                />
                
                <!-- 表格预览 -->
                <el-table 
                  :data="previewData" 
                  border 
                  stripe
                  max-height="400"
                  style="width: 100%;"
                >
                  <el-table-column
                    v-for="field in allSelectedFields"
                    :key="field"
                    :prop="field"
                    :label="field"
                    width="150"
                    show-overflow-tooltip
                  />
                </el-table>
              </div>
              
              <div v-else class="preview-empty">
                <el-empty description="暂无数据" />
              </div>
            </div>
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { dataSourceAPI, reportAPI } from '@/api'
import { ElMessage } from 'element-plus'
import { Grid, Close, Loading } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const projectId = ref(route.query.project_id || '')
const reportId = ref(route.query.report_id || '')
const isEditMode = computed(() => !!reportId.value)

const datasources = ref([])
const objects = ref([])
const selectedDataSourceId = ref('')
const activeObjects = ref([])
const saving = ref(false)
const loadingPreview = ref(false)
const previewData = ref([])
const loadingReport = ref(false)

const reportConfig = reactive({
  name: '',
  datasource_id: '',
  object_name: '',
  fields: [],
  chart_type: 'bar',
  chart_config: {
    xFields: [],      // 改为数组，支持多个字段
    yFields: [],      // 改为数组，支持多个字段
    seriesFields: []  // 改为数组，支持多个字段
  },
  filter_config: {},
  description: ''
})

const fetchDataSources = async () => {
  if (!projectId.value) return
  
  try {
    const data = await dataSourceAPI.getDataSources({ project_id: projectId.value })
    datasources.value = data
    if (data.length > 0) {
      selectedDataSourceId.value = data[0].id
      loadObjects()
    }
  } catch (error) {
    ElMessage.error('获取数据源失败')
  }
}

const loadObjects = async () => {
  if (!selectedDataSourceId.value) return
  
  reportConfig.datasource_id = selectedDataSourceId.value
  
  try {
    const data = await dataSourceAPI.getObjects(selectedDataSourceId.value)
    objects.value = data
  } catch (error) {
    ElMessage.error('获取数据对象失败')
  }
}

const handleFieldDragStart = (event, field, objectName) => {
  event.dataTransfer.setData('field', JSON.stringify({ 
    name: field.name,
    label: field.label,
    type: field.type,
    objectName: objectName
  }))
}

const handleDrop = (event, targetField) => {
  event.preventDefault()
  const fieldData = JSON.parse(event.dataTransfer.getData('field'))
  
  // 添加字段到目标数组（避免重复）
  if (!reportConfig.chart_config[targetField].includes(fieldData.name)) {
    reportConfig.chart_config[targetField].push(fieldData.name)
  } else {
    ElMessage.warning(`字段 ${fieldData.name} 已存在`)
    return
  }
  
  // 设置对象名称（如果还未设置）
  if (!reportConfig.object_name) {
    reportConfig.object_name = fieldData.objectName
  } else if (reportConfig.object_name !== fieldData.objectName) {
    // 检查是否来自不同对象
    ElMessage.warning({
      message: `当前报表使用的是 "${reportConfig.object_name}" 对象，无法混用不同对象的字段。请先清空所有字段后再选择新对象。`,
      duration: 3000
    })
    reportConfig.chart_config[targetField].pop() // 移除刚添加的
    return
  }
  
  // 添加到字段列表
  if (!reportConfig.fields.includes(fieldData.name)) {
    reportConfig.fields.push(fieldData.name)
  }
}

const removeFieldFromArray = (fieldKey, index) => {
  const fieldName = reportConfig.chart_config[fieldKey][index]
  reportConfig.chart_config[fieldKey].splice(index, 1)
  
  // 检查该字段是否在其他配置中使用
  const usedInOtherConfig = Object.entries(reportConfig.chart_config).some(
    ([key, value]) => {
      if (key === fieldKey) return false
      return Array.isArray(value) && value.includes(fieldName)
    }
  )
  
  // 如果没有在其他地方使用，从字段列表移除
  if (!usedInOtherConfig) {
    const fieldIndex = reportConfig.fields.indexOf(fieldName)
    if (fieldIndex > -1) {
      reportConfig.fields.splice(fieldIndex, 1)
    }
  }
  
  // 检查是否所有字段都被清空，如果是则重置对象名称
  checkAndResetObject()
}

const removeFromFields = (fieldName) => {
  // 从所有配置数组中移除
  Object.keys(reportConfig.chart_config).forEach(key => {
    const configValue = reportConfig.chart_config[key]
    if (Array.isArray(configValue)) {
      const index = configValue.indexOf(fieldName)
      if (index > -1) {
        configValue.splice(index, 1)
      }
    }
  })
  
  // 从字段列表移除
  const index = reportConfig.fields.indexOf(fieldName)
  if (index > -1) {
    reportConfig.fields.splice(index, 1)
  }
  
  // 检查是否所有字段都被清空，如果是则重置对象名称
  checkAndResetObject()
}

// 检查并重置对象名称
const checkAndResetObject = () => {
  // 如果所有字段都被清空，重置对象名称，允许选择新对象
  if (reportConfig.fields.length === 0) {
    reportConfig.object_name = ''
    previewData.value = []  // 同时清空预览数据
  }
}

// 清空所有字段
const clearAllFields = () => {
  // 清空所有配置
  reportConfig.chart_config.xFields = []
  reportConfig.chart_config.yFields = []
  reportConfig.chart_config.seriesFields = []
  reportConfig.fields = []
  reportConfig.object_name = ''
  previewData.value = []
  
  ElMessage.success('已清空所有字段，可以选择新对象')
}

const handleSave = async () => {
  // 验证
  if (!reportConfig.name) {
    ElMessage.warning('请输入报表名称')
    return
  }
  
  if (!reportConfig.datasource_id) {
    ElMessage.warning('请选择数据源')
    return
  }
  
  if (!reportConfig.object_name) {
    ElMessage.warning('请选择数据对象')
    return
  }
  
  if (reportConfig.fields.length === 0) {
    ElMessage.warning('请至少选择一个字段')
    return
  }
  
  if (reportConfig.chart_config.xFields.length === 0 || reportConfig.chart_config.yFields.length === 0) {
    ElMessage.warning('请至少为X轴和Y轴各配置一个字段')
    return
  }
  
  saving.value = true
  try {
    if (isEditMode.value) {
      // 更新报表
      await reportAPI.updateReport(reportId.value, reportConfig)
      ElMessage.success('报表更新成功')
    } else {
      // 创建报表
      await reportAPI.createReport({
        ...reportConfig,
        project_id: projectId.value
      })
      ElMessage.success('报表创建成功')
    }
    
    router.back()
  } catch (error) {
    ElMessage.error(isEditMode.value ? '更新报表失败' : '创建报表失败')
  } finally {
    saving.value = false
  }
}

const handleCancel = () => {
  router.back()
}

// 计算属性：是否可以预览
const canPreview = computed(() => {
  return reportConfig.object_name && 
         (reportConfig.chart_config.xFields.length > 0 || 
          reportConfig.chart_config.yFields.length > 0)
})

// 计算属性：所有已选字段
const allSelectedFields = computed(() => {
  return reportConfig.fields
})

// 加载预览数据
const loadPreviewData = async () => {
  if (!canPreview.value) {
    ElMessage.warning('请先配置字段')
    return
  }
  
  loadingPreview.value = true
  try {
    const data = await dataSourceAPI.previewData(reportConfig.datasource_id, {
      object_name: reportConfig.object_name,
      fields: reportConfig.fields,
      limit: 20
    })
    
    previewData.value = data.data || []
    
    if (previewData.value.length === 0) {
      ElMessage.info('暂无数据')
    }
  } catch (error) {
    console.error('预览数据加载失败:', error)
    ElMessage.error('数据加载失败')
  } finally {
    loadingPreview.value = false
  }
}

// 监听字段变化，自动刷新预览
watch(() => reportConfig.fields.length, () => {
  if (canPreview.value && reportConfig.fields.length > 0) {
    loadPreviewData()
  }
}, { deep: true })

const loadExistingReport = async () => {
  if (!reportId.value) return
  
  loadingReport.value = true
  try {
    const report = await reportAPI.getReport(reportId.value)
    
    // 填充报表数据
    reportConfig.name = report.name
    reportConfig.datasource_id = report.datasource_id
    reportConfig.object_name = report.object_name
    reportConfig.fields = report.fields || []
    reportConfig.chart_type = report.chart_type
    reportConfig.chart_config = report.chart_config || { xFields: [], yFields: [], seriesFields: [] }
    reportConfig.description = report.description || ''
    
    // 设置数据源
    selectedDataSourceId.value = report.datasource_id
    
    // 加载对象列表
    await loadObjects()
    
    // 加载预览数据
    if (reportConfig.fields.length > 0) {
      await loadPreviewData()
    }
    
    ElMessage.success('报表加载成功')
  } catch (error) {
    console.error('加载报表失败:', error)
    ElMessage.error('加载报表失败')
  } finally {
    loadingReport.value = false
  }
}

onMounted(async () => {
  await fetchDataSources()
  if (isEditMode.value) {
    await loadExistingReport()
  }
})
</script>

<style scoped>
.report-designer {
  height: calc(100vh - 120px);
  background: #f5f5f5;
}

.designer-aside {
  background: white;
  border-right: 1px solid #e0e0e0;
  overflow-y: auto;
  padding: 20px;
}

.aside-header h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
}

.field-list {
  padding: 10px 0;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 8px;
  background: #f5f5f5;
  border-radius: 4px;
  cursor: move;
  transition: all 0.3s;
}

.field-item:hover {
  background: #e8e8e8;
  transform: translateX(2px);
}

.designer-header {
  background: white;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.designer-main {
  padding: 20px;
  overflow-y: auto;
}

.chart-type-selector {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.chart-type-selector h4 {
  margin: 0 0 15px 0;
}

.field-config-area {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.config-section {
  margin-bottom: 20px;
}

.config-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-header h4 {
  margin: 0;
  font-size: 14px;
}

.drop-zone {
  min-height: 80px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 15px;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  transition: all 0.3s;
}

.drop-zone:hover {
  border-color: #409EFF;
  background: #f0f9ff;
}

.drop-placeholder {
  color: #999;
  font-size: 14px;
}

.field-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
}

.field-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #409EFF;
  color: white;
  border-radius: 4px;
  font-size: 14px;
}

.field-chip .el-icon {
  cursor: pointer;
  font-size: 16px;
}

.field-chip .el-icon:hover {
  opacity: 0.8;
}

.preview-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.preview-header h4 {
  margin: 0;
}

.preview-container {
  min-height: 300px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 20px;
}

.preview-empty {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-loading {
  min-height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 15px;
  font-size: 16px;
  color: #409EFF;
}

.preview-loading .el-icon {
  font-size: 32px;
}

.preview-content {
  max-height: 500px;
  overflow: auto;
}
</style>

