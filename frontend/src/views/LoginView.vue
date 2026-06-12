<template>
  <div style="display:flex;align-items:center;justify-content:center;height:100vh;background:#f5f5f5">
    <n-card style="width:400px" :bordered="true">
      <h2 style="text-align:center;margin-bottom:24px">YOLO Trainer</h2>
      <n-tabs v-model:value="tab" animated>
        <n-tab-pane name="login" tab="登录">
          <n-form ref="loginRef" :model="loginForm" :rules="rules">
            <n-form-item label="用户名" path="username">
              <n-input v-model:value="loginForm.username" placeholder="请输入用户名" />
            </n-form-item>
            <n-form-item label="密码" path="password">
              <n-input v-model:value="loginForm.password" type="password" placeholder="请输入密码" show-password-on="click" />
            </n-form-item>
            <n-button type="primary" block :loading="loading" @click="handleLogin">登录</n-button>
          </n-form>
        </n-tab-pane>
        <n-tab-pane name="register" tab="注册">
          <n-form ref="regRef" :model="regForm" :rules="rules">
            <n-form-item label="用户名" path="username">
              <n-input v-model:value="regForm.username" placeholder="请输入用户名" />
            </n-form-item>
            <n-form-item label="邮箱" path="email">
              <n-input v-model:value="regForm.email" placeholder="请输入邮箱" />
            </n-form-item>
            <n-form-item label="密码" path="password">
              <n-input v-model:value="regForm.password" type="password" placeholder="请输入密码" show-password-on="click" />
            </n-form-item>
            <n-button type="primary" block :loading="loading" @click="handleRegister">注册</n-button>
          </n-form>
        </n-tab-pane>
      </n-tabs>
    </n-card>
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
