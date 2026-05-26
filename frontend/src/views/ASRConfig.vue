<template>
  <div class="asr-config-page">
    <div class="page-header">
      <h1>语音识别配置</h1>
      <p class="subtitle">配置阿里云通义千问语音识别服务</p>
    </div>

    <el-card class="config-card">
      <el-form
        :model="form"
        :rules="rules"
        ref="formRef"
        label-width="150px"
        v-loading="loading"
      >
        <el-alert
          title="配置说明"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        >
          <p>本系统使用阿里云通义千问语音识别服务进行会议录音转写。</p>
          <p>
            请前往
            <a
              href="https://help.aliyun.com/zh/model-studio/get-api-key"
              target="_blank"
              >阿里云百炼平台</a
            >
            获取API Key。
          </p>
        </el-alert>

        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            :placeholder="
              hasApiKey ? '留空保持原配置不变' : '请输入阿里云DashScope API Key'
            "
            style="width: 500px"
          >
            <template #prepend>sk-</template>
          </el-input>
          <div class="form-tip">
            <span v-if="hasApiKey" style="color: #67c23a"
              >✓ 已配置API Key，如需修改请重新输入</span
            >
            <span v-else>API Key格式: sk-xxxxxxxxxxxxxxxxxxxxxxxx</span>
          </div>
        </el-form-item>

        <el-form-item label="API地域" prop="base_url">
          <el-select
            v-model="form.base_url"
            placeholder="选择API地域"
            style="width: 500px"
          >
            <el-option
              label="北京地域 (推荐)"
              value="https://dashscope.aliyuncs.com/api/v1"
            />
            <el-option
              label="新加坡地域"
              value="https://dashscope-intl.aliyuncs.com/api/v1"
            />
          </el-select>
          <div class="form-tip">选择离您服务器最近的地域以获得更好的性能</div>
        </el-form-item>

        <el-form-item label="ASR模型" prop="model">
          <el-select
            v-model="form.model"
            placeholder="选择语音识别模型"
            style="width: 500px"
          >
            <el-option
              label="qwen3-asr-flash-filetrans (长音频)"
              value="qwen3-asr-flash-filetrans"
            />
            <el-option
              label="qwen3-asr-flash (短音频)"
              value="qwen3-asr-flash"
            />
          </el-select>
          <div class="form-tip">
            长音频模型支持最长12小时录音,短音频模型支持最长5分钟
          </div>
        </el-form-item>

        <el-form-item label="服务器公网地址" prop="server_base_url">
          <el-input
            v-model="form.server_base_url"
            placeholder="http://your-server.com:8000"
            style="width: 500px"
          >
            <template #prepend>http://</template>
          </el-input>
          <div class="form-tip">
            阿里云需要通过公网URL访问音频文件,请确保该地址可从公网访问
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="saving">
            保存配置
          </el-button>
          <el-button @click="handleTest" :loading="testing">
            测试连接
          </el-button>
          <el-button @click="loadConfig"> 重置 </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- OSS配置卡片 -->
    <el-card class="config-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>OSS对象存储配置</span>
          <el-tag type="info" size="small" style="margin-left: 10px"
            >可选</el-tag
          >
        </div>
      </template>
      <el-form
        :model="ossForm"
        :rules="ossRules"
        ref="ossFormRef"
        label-width="150px"
        v-loading="ossLoading"
      >
        <el-alert
          title="配置说明"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        >
          <p>配置OSS后,会议音频文件将上传到云存储,提供更稳定的公网访问。</p>
          <p>如不配置,系统将使用本地服务器地址(需确保公网可访问)。</p>
        </el-alert>

        <el-form-item label="OSS提供商" prop="provider">
          <el-select
            v-model="ossForm.provider"
            placeholder="选择OSS提供商"
            style="width: 500px"
            clearable
          >
            <el-option label="不使用OSS(本地)" value="" />
            <el-option label="阿里云OSS" value="aliyun" />
            <el-option label="腾讯云COS" value="tencent" />
          </el-select>
          <div class="form-tip">
            <span v-if="hasOssConfig" style="color: #67c23a">✓ 已配置OSS</span>
            <span v-else>选择云存储提供商,或留空使用本地服务器</span>
          </div>
        </el-form-item>

        <template v-if="ossForm.provider">
          <el-form-item label="Access Key ID" prop="access_key_id">
            <el-input
              v-model="ossForm.access_key_id"
              type="password"
              show-password
              :placeholder="
                hasOssConfig ? '留空保持原配置不变' : '请输入Access Key ID'
              "
              style="width: 500px"
            />
            <div class="form-tip">
              <span v-if="hasOssConfig" style="color: #67c23a"
                >✓ 已配置,如需修改请重新输入</span
              >
              <span v-else>OSS访问密钥ID</span>
            </div>
          </el-form-item>

          <el-form-item label="Access Key Secret" prop="access_key_secret">
            <el-input
              v-model="ossForm.access_key_secret"
              type="password"
              show-password
              :placeholder="
                hasOssConfig ? '留空保持原配置不变' : '请输入Access Key Secret'
              "
              style="width: 500px"
            />
            <div class="form-tip">
              <span v-if="hasOssConfig" style="color: #67c23a"
                >✓ 已配置,如需修改请重新输入</span
              >
              <span v-else>OSS访问密钥</span>
            </div>
          </el-form-item>

          <el-form-item label="Bucket名称" prop="bucket_name">
            <el-input
              v-model="ossForm.bucket_name"
              placeholder="请输入Bucket名称"
              style="width: 500px"
            />
            <div class="form-tip">存储桶名称</div>
          </el-form-item>

          <el-form-item label="区域" prop="region">
            <el-input
              v-model="ossForm.region"
              :placeholder="
                ossForm.provider === 'aliyun'
                  ? '如: cn-hangzhou'
                  : '如: ap-guangzhou'
              "
              style="width: 500px"
            />
            <div class="form-tip">
              {{
                ossForm.provider === "aliyun"
                  ? "阿里云区域,如: cn-hangzhou, cn-beijing"
                  : "腾讯云区域,如: ap-guangzhou, ap-beijing"
              }}
            </div>
          </el-form-item>

          <el-form-item label="自定义域名" prop="endpoint">
            <el-input
              v-model="ossForm.endpoint"
              placeholder="https://your-domain.com (可选)"
              style="width: 500px"
            />
            <div class="form-tip">如已绑定自定义域名,请填写,否则留空</div>
          </el-form-item>
        </template>

        <el-form-item>
          <el-button type="primary" @click="handleSaveOss" :loading="ossSaving">
            保存OSS配置
          </el-button>
          <el-button
            @click="handleTestOss"
            :loading="ossTesting"
            v-if="ossForm.provider"
          >
            测试连接
          </el-button>
          <el-button @click="loadOssConfig"> 重置 </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="info-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>使用说明</span>
        </div>
      </template>
      <el-steps direction="vertical" :active="3">
        <el-step title="获取API Key">
          <template #description>
            <p>
              1. 访问
              <a href="https://modelstudio.console.aliyun.com" target="_blank"
                >阿里云百炼控制台</a
              >
            </p>
            <p>2. 在左侧菜单选择"API-KEY管理"</p>
            <p>3. 创建新的API Key并复制保存</p>
          </template>
        </el-step>
        <el-step title="配置服务">
          <template #description>
            <p>1. 将获取的API Key填入上方表单</p>
            <p>2. 选择合适的地域和模型</p>
            <p>3. 配置服务器公网地址(用于音频文件访问)</p>
          </template>
        </el-step>
        <el-step title="测试并保存">
          <template #description>
            <p>1. 点击"测试连接"按钮验证配置</p>
            <p>2. 测试通过后点击"保存配置"</p>
            <p>3. 现在可以使用会议分析功能了</p>
          </template>
        </el-step>
      </el-steps>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import api from "@/api/axios";

const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const formRef = ref(null);
const hasApiKey = ref(false); // 标记是否已有API Key配置

const form = ref({
  api_key: "",
  base_url: "https://dashscope.aliyuncs.com/api/v1",
  model: "qwen3-asr-flash-filetrans",
  server_base_url: "http://localhost:8000",
});

// OSS配置相关
const ossLoading = ref(false);
const ossSaving = ref(false);
const ossTesting = ref(false);
const ossFormRef = ref(null);
const hasOssConfig = ref(false);

const ossForm = ref({
  provider: "",
  access_key_id: "",
  access_key_secret: "",
  bucket_name: "",
  region: "",
  endpoint: "",
});

const rules = {
  api_key: [
    // API Key不再是必填，如果已有配置可以不填
    { min: 20, message: "API Key长度不正确", trigger: "blur" },
  ],
  base_url: [{ required: true, message: "请选择API地域", trigger: "change" }],
  model: [{ required: true, message: "请选择ASR模型", trigger: "change" }],
  server_base_url: [
    { required: true, message: "请输入服务器公网地址", trigger: "blur" },
  ],
};

const ossRules = {
  bucket_name: [
    { required: false, message: "请输入Bucket名称", trigger: "blur" },
  ],
  region: [{ required: false, message: "请输入区域", trigger: "blur" }],
};

const loadConfig = async () => {
  loading.value = true;
  try {
    const response = await api.get("/config/asr");
    if (response.data) {
      // 只更新非敏感字段,不回填API Key
      if (response.data.base_url) {
        form.value.base_url = response.data.base_url;
      }
      if (response.data.model) {
        form.value.model = response.data.model;
      }
      if (response.data.server_base_url) {
        form.value.server_base_url = response.data.server_base_url;
      }
      // 检查是否已有API Key配置
      if (response.data.api_key_masked) {
        hasApiKey.value = true;
        ElMessage.info("已有API Key配置,如需修改请重新输入");
      }
    }
  } catch (error) {
    console.log("加载配置失败:", error);
    // 首次使用时可能没有配置,不显示错误
  } finally {
    loading.value = false;
  }
};

const handleSave = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    saving.value = true;
    try {
      await api.post("/config/asr", form.value);
      ElMessage.success("配置保存成功");
    } catch (error) {
      ElMessage.error(
        "保存失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      saving.value = false;
    }
  });
};

const handleTest = async () => {
  if (!form.value.api_key) {
    ElMessage.warning("请先输入API Key");
    return;
  }

  testing.value = true;
  try {
    const response = await api.post("/config/asr/test", {
      api_key: form.value.api_key,
      base_url: form.value.base_url,
    });

    if (response.success) {
      ElMessage.success("连接测试成功!");
    } else {
      ElMessage.error("连接测试失败: " + (response.message || "未知错误"));
    }
  } catch (error) {
    ElMessage.error(
      "测试失败: " + (error.response?.data?.detail || error.message)
    );
  } finally {
    testing.value = false;
  }
};

// OSS配置相关函数
const loadOssConfig = async () => {
  ossLoading.value = true;
  try {
    const response = await api.get("/config/oss");
    if (response.data) {
      if (response.data.provider) {
        ossForm.value.provider = response.data.provider;
      }
      if (response.data.bucket_name) {
        ossForm.value.bucket_name = response.data.bucket_name;
      }
      if (response.data.region) {
        ossForm.value.region = response.data.region;
      }
      if (response.data.endpoint) {
        ossForm.value.endpoint = response.data.endpoint;
      }
      // 检查是否已配置
      if (response.data.access_key_id_masked) {
        hasOssConfig.value = true;
      }
    }
  } catch (error) {
    console.log("加载OSS配置失败:", error);
  } finally {
    ossLoading.value = false;
  }
};

const handleSaveOss = async () => {
  if (!ossFormRef.value) return;

  await ossFormRef.value.validate(async (valid) => {
    if (!valid) return;

    ossSaving.value = true;
    try {
      await api.post("/config/oss", ossForm.value);
      ElMessage.success("OSS配置保存成功");
      hasOssConfig.value = true;
    } catch (error) {
      ElMessage.error(
        "保存失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      ossSaving.value = false;
    }
  });
};

const handleTestOss = async () => {
  if (!ossForm.value.provider) {
    ElMessage.warning("请先选择OSS提供商");
    return;
  }

  ossTesting.value = true;
  try {
    const response = await api.post("/config/oss/test", ossForm.value);

    // API返回的数据在response.data中，但axios拦截器已经返回了response.data
    // 所以这里直接访问response
    if (response.success) {
      ElMessage.success("OSS连接测试成功!");
    } else {
      ElMessage.error("OSS连接测试失败: " + (response.message || "未知错误"));
    }
  } catch (error) {
    ElMessage.error(
      "测试失败: " + (error.response?.data?.detail || error.message)
    );
  } finally {
    ossTesting.value = false;
  }
};

onMounted(() => {
  loadConfig();
  loadOssConfig();
});
</script>

<style scoped>
.asr-config-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  margin: 0 0 10px 0;
  font-size: 28px;
  color: #303133;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.config-card {
  margin-bottom: 20px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  line-height: 1.5;
}

.info-card {
  background: #f9fafc;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
}

:deep(.el-step__description) p {
  margin: 5px 0;
  font-size: 13px;
}

:deep(.el-step__description) a {
  color: #409eff;
  text-decoration: none;
}

:deep(.el-step__description) a:hover {
  text-decoration: underline;
}

:deep(.el-alert) p {
  margin: 5px 0;
  font-size: 13px;
}

:deep(.el-alert) a {
  color: #409eff;
  text-decoration: none;
  font-weight: 500;
}

:deep(.el-alert) a:hover {
  text-decoration: underline;
}
</style>
