<template>
  <n-config-provider>
    <n-layout has-sider v-if="userStore.token" style="height: 100vh">
      <n-layout-sider bordered :width="220" :native-scrollbar="false">
        <div style="padding: 16px; font-size: 20px; font-weight: bold; text-align: center">
          YOLO Trainer
        </div>
        <n-menu :value="activeMenu" :options="menuOptions" @update:value="onMenuChange" />
        <div style="padding: 16px; text-align: center">
          <n-button quaternary @click="userStore.logout(); $router.push('/login')">
            退出登录
          </n-button>
        </div>
      </n-layout-sider>
      <n-layout>
        <n-layout-header bordered style="padding: 12px 24px; display: flex; align-items: center; justify-content: space-between">
          <span style="font-size: 16px; font-weight: 500">{{ currentTitle }}</span>
          <span style="color: #999">{{ userStore.username }}</span>
        </n-layout-header>
        <n-layout-content content-style="padding: 24px;" :native-scrollbar="false" style="height: calc(100vh - 56px)">
          <router-view />
        </n-layout-content>
      </n-layout>
    </n-layout>
    <router-view v-else />
  </n-config-provider>
</template>

<script setup>
import { computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NIcon } from 'naive-ui'
import { useUserStore } from './stores/user'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()

const titleMap = {
  '/': '仪表盘',
  '/training': '训练管理',
  '/models': '模型管理',
  '/datasets': '数据集管理',
  '/test': '测试中心',
}
const currentTitle = computed(() => titleMap[route.path] || 'YOLO Trainer')

const menuOptions = [
  { label: '仪表盘', key: '/' },
  { label: '训练管理', key: '/training' },
  { label: '模型管理', key: '/models' },
  { label: '数据集管理', key: '/datasets' },
  { label: '测试中心', key: '/test' },
]

const activeMenu = computed(() => {
  const p = route.path
  if (p.startsWith('/training')) return '/training'
  if (p.startsWith('/models')) return '/models'
  if (p.startsWith('/datasets')) return '/datasets'
  return p
})

function onMenuChange(key) {
  router.push(key)
}
</script>

<style>
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
</style>
