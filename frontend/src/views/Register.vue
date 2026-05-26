<template>
  <div class="register-container">
    <div class="register-box">
      <h1 class="title">用户注册</h1>
      <el-form
        :model="registerForm"
        :rules="rules"
        ref="formRef"
        class="register-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="邮箱"
            prefix-icon="Message"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="code" v-if="emailRequired">
          <div class="code-input-wrapper">
            <el-input
              v-model="registerForm.code"
              placeholder="邮箱验证码"
              prefix-icon="Key"
              size="large"
              style="flex: 1"
            />
            <el-button
              type="primary"
              plain
              size="large"
              :disabled="countdown > 0"
              @click="handleSendCode"
              class="send-code-btn"
            >
              {{ countdown > 0 ? `${countdown}s` : "获取验证码" }}
            </el-button>
          </div>
        </el-form-item>
        <el-form-item prop="full_name">
          <el-input
            v-model="registerForm.full_name"
            placeholder="姓名"
            prefix-icon="UserFilled"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="确认密码"
            prefix-icon="Lock"
            size="large"
            @keyup.enter="handleRegister"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleRegister"
            style="width: 100%"
          >
            注册
          </el-button>
        </el-form-item>
        <div class="login-link">
          已有账号？<router-link to="/login">立即登录</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { useUserStore } from "@/stores/user";
import { Message, Lock, User, UserFilled, Key } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { emailConfigAPI } from "@/api";

const userStore = useUserStore();
const formRef = ref();
const loading = ref(false);
const emailRequired = ref(false);
const countdown = ref(0);
let timer = null;

const registerForm = reactive({
  username: "",
  email: "",
  full_name: "",
  password: "",
  confirmPassword: "",
  role: "external_personnel",
  code: "",
});

const validatePassword = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error("两次输入的密码不一致"));
  } else {
    callback();
  }
};

const checkEmailStatus = async () => {
  try {
    const data = await emailConfigAPI.getStatus();
    emailRequired.value = data.enabled;
  } catch (err) {
    console.error("获取邮件配置状态失败", err);
  }
};

const handleSendCode = async () => {
  if (!registerForm.email) {
    return ElMessage.warning("请先输入邮箱");
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(registerForm.email)) {
    return ElMessage.warning("请输入有效的邮箱地址");
  }

  try {
    await emailConfigAPI.sendCode({
      email: registerForm.email,
      purpose: "register",
    });
    ElMessage.success("验证码已发送至您的邮箱");
    startCountdown();
  } catch (err) {
    // 错误已经在 axios 拦截器中处理
  }
};

const startCountdown = () => {
  countdown.value = 60;
  timer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      clearInterval(timer);
    }
  }, 1000);
};

const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  email: [
    { required: true, message: "请输入邮箱", trigger: "blur" },
    { type: "email", message: "请输入有效的邮箱地址", trigger: "blur" },
  ],
  code: [
    { required: true, message: "请输入验证码", trigger: "blur" },
    { len: 6, message: "验证码为6位", trigger: "blur" },
  ],
  full_name: [{ required: true, message: "请输入姓名", trigger: "blur" }],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码长度至少6位", trigger: "blur" },
  ],
  confirmPassword: [
    { required: true, message: "请确认密码", trigger: "blur" },
    { validator: validatePassword, trigger: "blur" },
  ],
};

const handleRegister = async () => {
  const valid = await formRef.value.validate();
  if (!valid) return;

  loading.value = true;
  try {
    const { confirmPassword, ...data } = registerForm;
    // 如果不需要验证码，从数据中移除
    if (!emailRequired.value) {
      delete data.code;
    }
    await userStore.register(data);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  checkEmailStatus();
});
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

.register-box {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.title {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 28px;
}

.register-form {
  margin-top: 20px;
}

.login-link {
  text-align: center;
  color: #666;
  font-size: 14px;
}

.login-link a {
  color: #409eff;
  text-decoration: none;
}

.login-link a:hover {
  text-decoration: underline;
}

.code-input-wrapper {
  display: flex;
  gap: 12px;
  width: 100%;
}

.send-code-btn {
  width: 120px;
}
</style>

