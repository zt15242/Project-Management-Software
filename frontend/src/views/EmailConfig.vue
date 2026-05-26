<template>
  <div class="email-config-container animate-fade-in">
    <div class="header-section">
      <h2 class="page-title-glow">邮局服务配置</h2>
      <p class="subtitle">
        配置系统 SMTP 服务，用于发送注册验证码、通知提醒等邮件。
      </p>
    </div>

    <el-row :gutter="24">
      <el-col :span="14">
        <el-card class="glass-card config-form-card">
          <template #header>
            <div class="card-header">
              <span class="header-text"
                ><el-icon><Postcard /></el-icon> SMTP 服务器设置</span
              >
              <el-switch
                v-model="form.is_enabled"
                active-text="启用服务"
                inactive-text="禁用"
                inline-prompt
                @change="handleSave"
              />
            </div>
          </template>

          <el-form
            :model="form"
            :rules="rules"
            ref="formRef"
            label-position="top"
          >
            <el-row :gutter="20">
              <el-col :span="16">
                <el-form-item label="SMTP 服务器地址" prop="smtp_server">
                  <el-input
                    v-model="form.smtp_server"
                    placeholder="例如: smtp.qq.com"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="端口" prop="smtp_port">
                  <el-input-number
                    v-model="form.smtp_port"
                    :min="1"
                    :max="65535"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="验证用户名" prop="smtp_user">
                  <el-input
                    v-model="form.smtp_user"
                    placeholder="通常是您的邮箱地址"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="授权码/密码" prop="smtp_password">
                  <el-input
                    v-model="form.smtp_password"
                    type="password"
                    show-password
                    placeholder="请输入授权码"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="发件人邮箱" prop="sender_email">
              <el-input
                v-model="form.sender_email"
                placeholder="例如: service@yourdomain.com"
              />
            </el-form-item>

            <el-form-item label="安全连接" class="security-item">
              <el-checkbox v-model="form.use_tls"
                >使用 SSL/TLS 加密</el-checkbox
              >
              <div class="form-tip">
                通常端口 465 使用 SSL，端口 587/25 使用 TLS 或明文。
              </div>
            </el-form-item>

            <div class="form-actions">
              <el-button
                type="primary"
                :loading="saving"
                @click="handleSave"
                class="premium-btn"
              >
                保存配置
              </el-button>
            </div>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card class="glass-card test-card">
          <template #header>
            <div class="card-header">
              <span class="header-text"
                ><el-icon><Connection /></el-icon> 配置测试</span
              >
            </div>
          </template>

          <div class="test-content">
            <p class="test-tip">
              在保存设置后，您可以向指定邮箱发送一封测试邮件，以验证配置是否正确。
            </p>
            <el-input v-model="testEmail" placeholder="接收测试邮件的邮箱">
              <template #append>
                <el-button
                  :loading="testing"
                  @click="handleTest"
                  :disabled="!form.id"
                >
                  发送测试
                </el-button>
              </template>
            </el-input>
          </div>
        </el-card>

        <div class="info-alert animate-fade-in" style="margin-top: 24px">
          <el-icon><InfoFilled /></el-icon>
          <div class="info-text">
            <h4>关于注册验证</h4>
            <p>
              一旦启用邮局配置，系统将自动在<b>用户注册</b>页面开启邮箱验证逻辑。新用户必须输入正确的
              6 位验证码才能完成注册。
            </p>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { Postcard, Connection, InfoFilled } from "@element-plus/icons-vue";
import { emailConfigAPI } from "@/api";

const formRef = ref(null);
const saving = ref(false);
const testing = ref(false);
const testEmail = ref("");

const form = ref({
  id: "",
  smtp_server: "",
  smtp_port: 465,
  smtp_user: "",
  smtp_password: "",
  sender_email: "",
  use_tls: true,
  is_enabled: true,
});

const rules = {
  smtp_server: [
    { required: true, message: "请输入SMTP服务器地址", trigger: "blur" },
  ],
  smtp_port: [{ required: true, message: "请输入端口", trigger: "blur" }],
  smtp_user: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  smtp_password: [{ required: true, message: "请输入授权码", trigger: "blur" }],
  sender_email: [
    { required: true, message: "请输入发件人邮箱", trigger: "blur" },
    { type: "email", message: "邮箱格式不正确", trigger: "blur" },
  ],
};

const fetchConfig = async () => {
  try {
    const data = await emailConfigAPI.getConfig();
    if (data) {
      form.value = { ...data };
    }
  } catch (err) {
    console.error("获取配置失败", err);
  }
};

const handleSave = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true;
      try {
        const data = await emailConfigAPI.saveConfig(form.value);
        form.value.id = data.id;
        ElMessage.success("配置已保存");
      } catch (err) {
        // 错误已经在 axios 拦截器中处理
      } finally {
        saving.value = false;
      }
    }
  });
};

const handleTest = async () => {
  if (!testEmail.value) {
    return ElMessage.warning("请输入测试邮箱地址");
  }

  testing.value = true;
  try {
    await emailConfigAPI.testConfig({ test_email: testEmail.value });
    ElMessage.success("测试邮件已发送，请查收");
  } catch (err) {
    // 错误已经在 axios 拦截器中处理
  } finally {
    testing.value = false;
  }
};

onMounted(() => {
  fetchConfig();
});
</script>

<style scoped>
.email-config-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.header-section {
  margin-bottom: 32px;
}

.page-title-glow {
  font-size: 28px;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 8px;
}

.subtitle {
  color: #64748b;
  font-size: 15px;
}

.config-form-card,
.test-card {
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
  background: white !important;
  border: 1px solid #e2e8f0;
}

.header-text {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1e293b;
}

.security-item {
  margin-top: 10px;
}

.form-tip {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 8px;
  line-height: 1.4;
}

.form-actions {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-end;
}

.test-content {
  padding: 8px 0;
}

.test-tip {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 20px;
}

.info-alert {
  display: flex;
  gap: 16px;
  padding: 24px;
  background: #f8faff;
  border-radius: 12px;
  border: 1px solid #e0e7ff;
}

.info-alert .el-icon {
  font-size: 24px;
  color: #4f46e5;
}

.info-text h4 {
  margin: 0 0 8px 0;
  font-weight: 700;
  color: #1e293b;
}

.info-text p {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #475569;
}

.premium-btn {
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
  border: none !important;
  padding: 12px 32px;
  height: auto;
  font-weight: 600;
  color: white !important;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  transition: all 0.3s;
}

.premium-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
  opacity: 0.9;
}
</style>
