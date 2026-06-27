<template>
  <div class="login-page">
    <!-- Ambient warm orbs -->
    <div class="bg-orb orb-1"></div>
    <div class="bg-orb orb-2"></div>

    <div class="login-card">
      <div class="login-brand">
        <div class="brand-mark">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor" opacity="0.9"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.7"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/>
          </svg>
        </div>
        <h1>YOLO Trainer</h1>
        <p>模型训练管理平台</p>
      </div>

      <n-tabs v-model:value="tab" animated type="line" justify-content="center" class="login-tabs">
        <n-tab-pane name="login" tab="登录">
          <n-form ref="loginRef" :model="loginForm" :rules="rules" label-placement="top" size="large">
            <n-form-item path="username">
              <n-input v-model:value="loginForm.username" placeholder="用户名" clearable :input-props="{ autocomplete: 'username' }" />
            </n-form-item>
            <n-form-item path="password">
              <n-input v-model:value="loginForm.password" type="password" placeholder="密码" show-password-on="click" :input-props="{ autocomplete: 'current-password' }" @keyup.enter="handleLogin" />
            </n-form-item>
            <n-button type="primary" block :loading="loading" size="large" @click="handleLogin" class="login-btn">
              登录
            </n-button>
          </n-form>
        </n-tab-pane>
        <n-tab-pane name="register" tab="注册">
          <n-form ref="regRef" :model="regForm" :rules="rules" label-placement="top" size="large">
            <n-form-item path="username">
              <n-input v-model:value="regForm.username" placeholder="用户名" clearable />
            </n-form-item>
            <n-form-item path="email">
              <n-input v-model:value="regForm.email" placeholder="邮箱" clearable />
            </n-form-item>
            <n-form-item path="password">
              <n-input v-model:value="regForm.password" type="password" placeholder="密码（至少8位）" show-password-on="click" />
            </n-form-item>
            <n-button type="primary" block :loading="loading" size="large" @click="handleRegister" class="login-btn">
              注册
            </n-button>
          </n-form>
        </n-tab-pane>
      </n-tabs>
    </div>

    <div class="login-footer">
      YOLO Trainer &copy; 2025
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const router = useRouter()
const message = useMessage()

const tab = ref('login')
const loading = ref(false)
const loginRef = ref(null)
const regRef = ref(null)

const loginForm = ref({ username: '', password: '' })
const regForm = ref({ username: '', email: '', password: '' })

const rules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur' },
  email: { required: true, message: '请输入邮箱', trigger: 'blur' },
}

async function handleLogin() {
  try {
    loading.value = true
    await userStore.login(loginForm.value)
    message.success('登录成功')
    router.push('/')
  } catch (e) {
    message.error(e?.message || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  try {
    loading.value = true
    await userStore.register(regForm.value)
    message.success('注册成功，请登录')
    tab.value = 'login'
  } catch (e) {
    message.error(e?.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ── Page ── */
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #F7F5F0;
  position: relative;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}

/* ── Ambient warm orbs ── */
.bg-orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}
.orb-1 {
  top: -160px;
  right: -100px;
  width: 520px;
  height: 520px;
  background: radial-gradient(circle at 60% 40%, rgba(199, 133, 58, 0.07) 0%, rgba(218, 154, 80, 0.03) 35%, transparent 70%);
}
.orb-2 {
  bottom: -120px;
  left: -80px;
  width: 380px;
  height: 380px;
  background: radial-gradient(circle at 40% 60%, rgba(199, 133, 58, 0.05) 0%, transparent 70%);
}

/* ── Card ── */
.login-card {
  width: 420px;
  background: #FFFFFF;
  border-radius: 16px;
  padding: 48px 44px 40px;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.03),
    0 8px 24px rgba(0, 0, 0, 0.04),
    0 0 0 1px rgba(199, 133, 58, 0.04),
    0 4px 32px rgba(199, 133, 58, 0.05);
  border: 1px solid #EEEBE6;
  z-index: 1;
  transition: box-shadow 0.3s ease;
}

/* ── Brand ── */
.login-brand {
  text-align: center;
  margin-bottom: 36px;
}
.brand-mark {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #C7853A 0%, #DA9A50 100%);
  color: #FFF;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(199, 133, 58, 0.25);
}
.login-brand h1 {
  font-size: 26px;
  font-weight: 700;
  color: #2D2A26;
  margin: 0 0 8px;
  letter-spacing: -0.3px;
  line-height: 1.3;
}
.login-brand p {
  font-size: 14px;
  color: #A09890;
  margin: 0;
  font-weight: 400;
  letter-spacing: 0.3px;
}

/* ── Tabs ── */
.login-tabs {
  margin-top: 0;
}

/* ── Form spacing ── */
.login-tabs :deep(.n-form-item) {
  margin-bottom: 20px;
}

/* ── Inputs: large & inviting ── */
.login-tabs :deep(.n-input) {
  --n-border: 1px solid #E8E5DF;
  --n-border-radius: 10px;
  --n-border-hover: 1px solid #D4CFC7;
  --n-border-focus: 1px solid #C7853A;
  --n-box-shadow-focus: 0 0 0 3px rgba(199, 133, 58, 0.1);
  --n-color: #FFFFFF;
  --n-color-focus: #FFFFFF;
}
.login-tabs :deep(.n-input .n-input__input-el) {
  font-size: 15px;
  color: #2D2A26;
}
.login-tabs :deep(.n-input .n-input__placeholder span) {
  color: #B8B0A6;
  font-size: 14px;
}
.login-tabs :deep(.n-base-clear) {
  color: #B8B0A6;
}

/* ── Button: subtle gradient ── */
.login-btn {
  margin-top: 8px !important;
}
.login-tabs :deep(.n-button--primary-type) {
  --n-color: #C7853A;
  --n-color-hover: #DA9A50;
  --n-color-pressed: #A86E2E;
  --n-color-focus: #C7853A;
  --n-border: 1px solid transparent;
  --n-border-hover: 1px solid transparent;
  --n-border-pressed: 1px solid transparent;
  --n-border-focus: 1px solid transparent;
  --n-border-radius: 10px;
  --n-text-color: #FFFFFF;
  --n-text-color-hover: #FFFFFF;
  --n-text-color-pressed: #FFFFFF;
  --n-text-color-focus: #FFFFFF;
  --n-ripple-color: rgba(255, 255, 255, 0.3);
  background: linear-gradient(135deg, #C7853A 0%, #DA9A50 100%) !important;
  font-weight: 600;
  font-size: 15px;
  letter-spacing: 0.5px;
  height: 44px;
  box-shadow: 0 2px 8px rgba(199, 133, 58, 0.2);
  transition: all 0.25s ease;
}
.login-tabs :deep(.n-button--primary-type:hover) {
  background: linear-gradient(135deg, #D49445 0%, #E0A85E 100%) !important;
  box-shadow: 0 4px 16px rgba(199, 133, 58, 0.3);
  transform: translateY(-1px);
}
.login-tabs :deep(.n-button--primary-type:active) {
  background: linear-gradient(135deg, #A86E2E 0%, #C7853A 100%) !important;
  box-shadow: 0 1px 4px rgba(199, 133, 58, 0.15);
  transform: translateY(0);
}

/* ── Tabs styling ── */
.login-tabs :deep(.n-tabs-nav) {
  margin-bottom: 28px;
}
.login-tabs :deep(.n-tabs-tab) {
  color: #A09890;
  font-size: 15px;
  font-weight: 500;
  padding: 6px 0;
  transition: color 0.2s ease;
}
.login-tabs :deep(.n-tabs-tab--active) {
  color: #C7853A;
  font-weight: 600;
}
.login-tabs :deep(.n-tabs-bar) {
  background: #C7853A;
  height: 2px;
  border-radius: 1px;
}

/* ── Footer ── */
.login-footer {
  margin-top: 36px;
  font-size: 12px;
  color: #B8B0A6;
  z-index: 1;
  letter-spacing: 0.3px;
}
</style>
