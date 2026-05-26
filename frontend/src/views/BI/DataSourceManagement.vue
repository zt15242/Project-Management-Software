<template>
  <div class="datasource-management">
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="showCreateDialog">创建数据源</el-button>
    </div>

    <el-table :data="datasources" border style="width: 100%; margin-top: 20px;">
      <el-table-column prop="name" label="数据源名称" width="200" />
      <el-table-column prop="type" label="类型" width="120">
        <template #default="{ row }">
          <el-tag>{{ getTypeLabel(row.type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="配置" width="150">
        <template #default="{ row }">
          <el-tag v-if="isUsingSystemConfig(row)" type="success" size="small">
            系统默认配置
          </el-tag>
          <el-tag v-else type="info" size="small">
            自定义配置
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" link @click="handleEdit(row)">编辑</el-button>
          <el-button type="danger" size="small" link @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建/编辑数据源对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
    >
      <el-form :model="datasourceForm" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="数据源名称" prop="name">
          <el-input v-model="datasourceForm.name" placeholder="请输入数据源名称" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="datasourceForm.type" placeholder="选择数据源类型" style="width: 100%">
            <el-option 
              v-for="dsType in enabledDataSourceTypes" 
              :key="dsType.value"
              :label="dsType.label" 
              :value="dsType.value" 
            />
          </el-select>
          <div v-if="enabledDataSourceTypes.length === 0" class="form-tip">
            系统未配置可用的数据源类型，请联系管理员
          </div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="datasourceForm.description" type="textarea" :rows="2" />
        </el-form-item>
        
        <!-- MongoDB类型配置 -->
        <template v-if="datasourceForm.type === 'mongodb'">
          <el-form-item label="配置方式">
            <el-radio-group v-model="useSystemConfig">
              <el-radio :label="true">使用系统默认配置</el-radio>
              <el-radio :label="false">自定义配置</el-radio>
            </el-radio-group>
          </el-form-item>
          
          <template v-if="!useSystemConfig">
            <el-form-item label="主机" prop="config.host">
              <el-input v-model="datasourceForm.config.host" placeholder="例如: localhost" />
            </el-form-item>
            <el-form-item label="端口" prop="config.port">
              <el-input v-model="datasourceForm.config.port" placeholder="例如: 27017" />
            </el-form-item>
            <el-form-item label="数据库名" prop="config.database">
              <el-input v-model="datasourceForm.config.database" />
            </el-form-item>
            <el-form-item label="用户名">
              <el-input v-model="datasourceForm.config.username" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="datasourceForm.config.password" type="password" show-password />
            </el-form-item>
          </template>
          
          <el-alert 
            v-if="useSystemConfig" 
            title="将使用系统MongoDB配置，无需填写连接信息" 
            type="success" 
            :closable="false"
            style="margin-bottom: 15px;"
          />
        </template>
        
        <!-- 其他数据库类型配置 -->
        <template v-if="['mysql', 'postgresql'].includes(datasourceForm.type)">
          <el-form-item label="主机" prop="config.host">
            <el-input v-model="datasourceForm.config.host" placeholder="例如: localhost" />
          </el-form-item>
          <el-form-item label="端口" prop="config.port">
            <el-input v-model="datasourceForm.config.port" placeholder="例如: 3306" />
          </el-form-item>
          <el-form-item label="数据库名" prop="config.database">
            <el-input v-model="datasourceForm.config.database" />
          </el-form-item>
          <el-form-item label="用户名" prop="config.username">
            <el-input v-model="datasourceForm.config.username" />
          </el-form-item>
          <el-form-item label="密码" prop="config.password">
            <el-input v-model="datasourceForm.config.password" type="password" show-password />
          </el-form-item>
        </template>

        <!-- API类型配置 -->
        <template v-if="datasourceForm.type === 'api'">
          <el-form-item label="API地址" prop="config.url">
            <el-input v-model="datasourceForm.config.url" placeholder="例如: https://api.example.com" />
          </el-form-item>
          <el-form-item label="认证Token">
            <el-input v-model="datasourceForm.config.token" />
          </el-form-item>
        </template>

        <!-- CSV类型配置 -->
        <template v-if="datasourceForm.type === 'csv'">
          <el-form-item label="文件路径" prop="config.path">
            <el-input v-model="datasourceForm.config.path" placeholder="例如: /path/to/data.csv" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed, onMounted } from 'vue'
import { dataSourceAPI, biConfigAPI } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const props = defineProps({
  projectId: String
})

const datasources = ref([])
const enabledDataSourceTypes = ref([])
const dialogVisible = ref(false)
const formRef = ref()
const submitting = ref(false)
const isEdit = ref(false)
const currentDatasource = ref(null)
const useSystemConfig = ref(true) // 默认使用系统配置

const datasourceForm = reactive({
  name: '',
  type: 'mongodb',
  description: '',
  config: {}
})

const rules = {
  name: [{ required: true, message: '请输入数据源名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择数据源类型', trigger: 'change' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑数据源' : '创建数据源')

const getTypeLabel = (type) => {
  const labels = {
    mysql: 'MySQL',
    postgresql: 'PostgreSQL',
    mongodb: 'MongoDB',
    api: 'API接口',
    csv: 'CSV文件'
  }
  return labels[type] || type
}

const isUsingSystemConfig = (datasource) => {
  return datasource.config && datasource.config.use_system === true
}

const formatDateTime = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const fetchEnabledDataSourceTypes = async () => {
  try {
    const data = await biConfigAPI.getEnabledDataSourceTypes()
    enabledDataSourceTypes.value = data.enabled_types
    
    // 设置默认类型为第一个启用的类型
    if (enabledDataSourceTypes.value.length > 0 && !isEdit.value) {
      datasourceForm.type = enabledDataSourceTypes.value[0].value
    }
  } catch (error) {
    ElMessage.error('获取数据源类型配置失败')
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

const showCreateDialog = () => {
  isEdit.value = false
  const defaultType = enabledDataSourceTypes.value.length > 0 
    ? enabledDataSourceTypes.value[0].value 
    : 'mongodb'
  
  useSystemConfig.value = true // 默认使用系统配置
  
  Object.assign(datasourceForm, {
    name: '',
    type: defaultType,
    description: '',
    config: {}
  })
  dialogVisible.value = true
}

const handleEdit = (datasource) => {
  isEdit.value = true
  currentDatasource.value = datasource
  
  // 判断是否使用系统配置（config为空或包含use_system字段）
  const hasConfig = datasource.config && Object.keys(datasource.config).length > 0
  const isUsingSystemConfig = !hasConfig || datasource.config.use_system === true
  
  useSystemConfig.value = isUsingSystemConfig
  
  Object.assign(datasourceForm, {
    name: datasource.name,
    type: datasource.type,
    description: datasource.description,
    config: hasConfig ? { ...datasource.config } : {}
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate()
  if (!valid) return
  
  submitting.value = true
  try {
    // 如果MongoDB使用系统配置，设置特殊标记
    const config = datasourceForm.type === 'mongodb' && useSystemConfig.value
      ? { use_system: true }
      : datasourceForm.config
    
    const data = {
      name: datasourceForm.name,
      type: datasourceForm.type,
      description: datasourceForm.description,
      config: config,
      project_id: props.projectId
    }
    
    if (isEdit.value) {
      await dataSourceAPI.updateDataSource(currentDatasource.value.id, data)
      ElMessage.success('数据源更新成功')
    } else {
      await dataSourceAPI.createDataSource(data)
      ElMessage.success('数据源创建成功')
    }
    
    dialogVisible.value = false
    fetchDataSources()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (datasource) => {
  try {
    await ElMessageBox.confirm('确定要删除此数据源吗？', '提示', {
      type: 'warning'
    })
    
    await dataSourceAPI.deleteDataSource(datasource.id)
    ElMessage.success('删除成功')
    fetchDataSources()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

watch(() => props.projectId, fetchDataSources, { immediate: true })

onMounted(() => {
  fetchEnabledDataSourceTypes()
})
</script>

<style scoped>
.datasource-management {
  padding: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}
</style>

