<template>
  <div class="ai-config-page">
    <div class="page-header">
      <h1>AI平台配置</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        添加AI平台
      </el-button>
    </div>

    <!-- AI配置列表 -->
    <el-card class="config-list">
      <el-table :data="configs" v-loading="loading" stripe>
        <el-table-column prop="provider" label="AI平台" width="150">
          <template #default="{ row }">
            <el-tag :type="getProviderType(row.provider)">
              {{ getProviderName(row.provider) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model" label="模型" width="180" />
        <el-table-column prop="api_key_masked" label="API Key" width="200">
          <template #default="{ row }">
            <code>{{ row.api_key_masked }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="base_url" label="API地址" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="150" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_enabled"
              @change="toggleEnabled(row)"
              :disabled="row.is_enabled"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showEditDialog(row)"
              >编辑</el-button
            >
            <el-button link type="success" @click="testConfig(row)"
              >测试</el-button
            >
            <el-button link type="danger" @click="handleDelete(row)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="isEdit ? '编辑AI配置' : '添加AI平台'"
      width="600px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="AI平台" prop="provider">
          <el-select
            v-model="form.provider"
            placeholder="选择AI平台"
            :disabled="isEdit"
            style="width: 100%"
          >
            <el-option label="规则匹配（默认）" value="none" />
            <el-option label="OpenAI GPT" value="openai" />
            <el-option label="通义千问" value="qwen" />
            <el-option label="智谱AI" value="zhipu" />
            <el-option label="Claude" value="claude" />
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="Gemini" value="gemini" />
          </el-select>
        </el-form-item>
        <el-form-item
          label="API Key"
          prop="api_key"
          v-if="form.provider !== 'none'"
        >
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            :placeholder="isEdit ? '留空保持原值不变' : '请输入API Key'"
          />
          <div class="form-tip" v-if="isEdit">留空则保持原API Key不变</div>
        </el-form-item>
        <el-form-item
          label="模型名称"
          prop="model"
          v-if="form.provider !== 'none'"
        >
          <el-input
            v-model="form.model"
            placeholder="如: gpt-4, qwen-max, glm-4"
          />
          <div class="form-tip">留空使用默认模型</div>
        </el-form-item>
        <el-form-item
          label="API地址"
          prop="base_url"
          v-if="form.provider !== 'none'"
        >
          <el-input
            v-model="form.base_url"
            placeholder="自定义API地址（可选）"
          />
          <div class="form-tip">留空使用官方API</div>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="描述信息（可选）"
          />
        </el-form-item>
        <el-form-item label="启用" prop="is_enabled">
          <el-switch v-model="form.is_enabled" />
          <div class="form-tip">启用后将使用此AI平台进行代码分析</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting"
          >保存</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus } from "@element-plus/icons-vue";
import { aiConfigAPI } from "@/api";

const configs = ref([]);
const loading = ref(false);
const submitting = ref(false);
const showDialog = ref(false);
const showCreateDialog = computed({
  get: () => showDialog.value && !isEdit.value,
  set: (val) => {
    if (val) {
      isEdit.value = false;
      form.value = {
        provider: "none",
        api_key: "",
        model: "",
        base_url: "",
        description: "",
        is_enabled: false,
      };
      showDialog.value = true;
    }
  },
});
const isEdit = ref(false);
const currentConfig = ref(null);

const form = ref({
  provider: "none",
  api_key: "",
  model: "",
  base_url: "",
  description: "",
  is_enabled: false,
});

const formRef = ref(null);

const rules = computed(() => ({
  provider: [{ required: true, message: "请选择AI平台", trigger: "change" }],
  api_key: [
    {
      required: !isEdit.value,
      message: "请输入API Key",
      trigger: "blur",
    },
  ],
}));

const getProviderName = (provider) => {
  const nameMap = {
    none: "规则匹配",
    openai: "OpenAI",
    qwen: "通义千问",
    zhipu: "智谱AI",
    claude: "Claude",
    deepseek: "DeepSeek",
    gemini: "Gemini",
  };
  return nameMap[provider] || provider;
};

const getProviderType = (provider) => {
  const typeMap = {
    none: "",
    openai: "success",
    qwen: "primary",
    zhipu: "warning",
    claude: "danger",
    deepseek: "info",
    gemini: "success",
  };
  return typeMap[provider] || "";
};

const loadConfigs = async () => {
  loading.value = true;
  try {
    const res = await aiConfigAPI.getConfigs();
    configs.value = res || [];
  } catch (error) {
    ElMessage.error(
      "加载AI配置失败：" + (error.response?.data?.detail || error.message)
    );
  } finally {
    loading.value = false;
  }
};

const showEditDialog = (config) => {
  isEdit.value = true;
  currentConfig.value = config;
  form.value = {
    provider: config.provider,
    api_key: "", // 不显示原始API Key
    model: config.model || "",
    base_url: config.base_url || "",
    description: config.description || "",
    is_enabled: config.is_enabled,
  };
  showDialog.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    submitting.value = true;
    try {
      // 如果没有修改API Key，就不发送
      const submitData = { ...form.value };
      if (isEdit.value && submitData.api_key === "") {
        delete submitData.api_key;
      }

      if (isEdit.value) {
        await aiConfigAPI.updateConfig(currentConfig.value.id, submitData);
        ElMessage.success("更新成功");
      } else {
        await aiConfigAPI.createConfig(submitData);
        ElMessage.success("添加成功");
      }

      showDialog.value = false;
      loadConfigs();
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || "操作失败");
    } finally {
      submitting.value = false;
    }
  });
};

const toggleEnabled = async (config) => {
  try {
    await aiConfigAPI.updateConfig(config.id, {
      is_enabled: config.is_enabled,
    });
    ElMessage.success(config.is_enabled ? "已启用" : "已禁用");
    loadConfigs();
  } catch (error) {
    config.is_enabled = !config.is_enabled; // 恢复状态
    ElMessage.error(error.response?.data?.detail || "操作失败");
  }
};

const testConfig = async (config) => {
  try {
    const res = await aiConfigAPI.testConfig(config.id);
    if (res.success) {
      ElMessage.success("连接测试成功");
    } else {
      ElMessage.error("连接测试失败");
    }
  } catch (error) {
    ElMessage.error(
      "连接测试失败：" + (error.response?.data?.detail || error.message)
    );
  }
};

const handleDelete = async (config) => {
  ElMessageBox.confirm(
    `确定要删除 "${getProviderName(config.provider)}" 配置吗？`,
    "确认删除",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    }
  )
    .then(async () => {
      try {
        await aiConfigAPI.deleteConfig(config.id);
        ElMessage.success("删除成功");
        loadConfigs();
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || "删除失败");
      }
    })
    .catch(() => {});
};

onMounted(() => {
  loadConfigs();
});
</script>

<style scoped>
.ai-config-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
}

.config-list {
  min-height: 400px;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: "Courier New", monospace;
}
</style>

