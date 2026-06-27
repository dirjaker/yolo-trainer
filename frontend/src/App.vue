<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-layout has-sider v-if="userStore.token" style="height: 100vh">
        <!-- Sidebar -->
        <n-layout-sider bordered :width="220" :native-scrollbar="false" class="app-sidebar">
          <div class="sidebar-brand">
            <div class="brand-logo">Y</div>
            <div class="brand-text">
              <span class="brand-name">YOLO Trainer</span>
              <span class="brand-sub">模型训练平台</span>
            </div>
          </div>
          <n-menu
            :value="activeMenu"
            :options="menuOptions"
            @update:value="onMenuChange"
            :root-indent="20"
            :indent="16"
          />
          <div class="sidebar-footer">
            <div class="sidebar-user">
              <n-avatar :size="30" round class="user-avatar">
                {{ (userStore.username || 'U')[0].toUpperCase() }}
              </n-avatar>
              <div class="user-meta">
                <span class="user-name">{{ userStore.username }}</span>
                <span class="user-role">管理员</span>
              </div>
            </div>
            <n-button text size="tiny" @click="userStore.logout(); $router.push('/login')" class="logout-btn">
              退出登录
            </n-button>
          </div>
        </n-layout-sider>
        <!-- Main -->
        <n-layout class="main-layout">
          <n-layout-header bordered class="app-header">
            <span class="header-title">{{ currentTitle }}</span>
          </n-layout-header>
          <n-layout-content class="app-content">
            <router-view v-slot="{ Component }">
              <transition name="page-fade" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>
          </n-layout-content>
        </n-layout>
      </n-layout>
      <router-view v-else />
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from './stores/user'
import { menuIcons } from './utils/icons'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()

// Theme overrides — refined warm minimal
const themeOverrides = {
  common: {
    primaryColor: '#C7853A',
    primaryColorHover: '#DA9A50',
    primaryColorPressed: '#A86E2E',
    primaryColorSuppl: '#E8C090',
    borderRadius: '12px',
    borderRadiusSmall: '10px',
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif",
  },
  Button: {
    borderRadiusMedium: '12px',
    borderRadiusSmall: '10px',
  },
  Card: {
    borderRadius: '16px',
    color: '#FFFFFF',
    borderColor: '#EEEBE6',
    titleTextColor: '#2D2A26',
    titleFontWeight: '600',
    paddingMedium: '28px',
  },
  Menu: {
    borderRadius: '10px',
    itemColorActive: '#FDF8F2',
    itemTextColorActive: '#C7853A',
    itemColorActiveHover: '#FDF6EE',
    itemColorHover: '#F8F4EE',
    itemTextColor: '#5C5550',
    itemTextColorHover: '#C7853A',
    groupTextColor: '#A09890',
    arrowColor: '#C5BFB8',
    itemHeight: '44px',
    fontSize: '13.5px',
  },
  Tag: {
    borderRadius: '8px',
  },
  Input: {
    borderRadius: '12px',
    borderHover: '#D5C8B6',
    borderFocus: '#C7853A',
  },
  Layout: {
    siderBorderColor: '#EEEBE6',
  },
}

const titleMap = {
  '/': '仪表盘',
  '/training': '训练管理',
  '/models': '模型管理',
  '/datasets': '数据集管理',
  '/test': '测试中心',
  '/compare': '模型对比',
  '/deploy': '模型部署',
  '/hyperparameter': '超参搜索',
  '/team': '团队管理',
  '/activity': '活动日志',
}

const menuOptions = Object.entries(titleMap).map(([key, label]) => ({
  label,
  key,
  icon: menuIcons[key] ? () => h(menuIcons[key]) : undefined,
}))

const currentTitle = computed(() => titleMap[route.path] || 'YOLO Trainer')
const activeMenu = computed(() => {
  const p = route.path
  if (p.startsWith('/training')) return '/training'
  if (p.startsWith('/models')) return '/models'
  if (p.startsWith('/datasets')) return '/datasets'
  if (p.startsWith('/compare')) return '/compare'
  if (p.startsWith('/deploy')) return '/deploy'
  if (p.startsWith('/hyperparameter')) return '/hyperparameter'
  if (p.startsWith('/team')) return '/team'
  if (p.startsWith('/activity')) return '/activity'
  return p
})

function onMenuChange(key) {
  router.push(key)
}
</script>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
  background: #F7F5F0;
  color: #2D2A26;
  -webkit-font-smoothing: antialiased;
}

/* Sidebar */
.app-sidebar {
  background: #FBFAF8 !important;
}
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 22px 20px 18px;
  border-bottom: 1px solid #F0EDE8;
  margin-bottom: 4px;
}
.brand-logo {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #C7853A 0%, #DA9A50 100%);
  color: #FFF;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 16px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(199, 133, 58, 0.2);
}
.brand-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.brand-name {
  font-size: 15px;
  font-weight: 700;
  color: #2D2A26;
  letter-spacing: -0.2px;
  line-height: 1.2;
}
.brand-sub {
  font-size: 11px;
  color: #A09890;
  font-weight: 400;
}
.sidebar-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 14px 16px;
  border-top: 1px solid #F0EDE8;
  background: #FBFAF8;
}
.sidebar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.user-avatar {
  background: linear-gradient(135deg, #C7853A, #DA9A50) !important;
  color: #FFF !important;
  font-weight: 600;
  flex-shrink: 0;
}
.user-meta {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}
.user-meta .user-name {
  font-size: 13px;
  font-weight: 500;
  color: #3D3833;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.user-meta .user-role {
  font-size: 11px;
  color: #A09890;
}
.logout-btn {
  font-size: 12px;
  color: #A09890;
}
.logout-btn:hover {
  color: #C7853A;
}

/* Header */
.main-layout {
  background: #F7F5F0;
}
.app-header {
  padding: 0 32px;
  height: 56px;
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid #EEEBE6;
}
.header-title {
  font-size: 15px;
  font-weight: 600;
  color: #2D2A26;
  letter-spacing: -0.2px;
}

/* Content */
.app-content {
  padding: 32px;
  background: #F7F5F0;
}

/* Page transitions */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.page-fade-leave-to {
  opacity: 0;
}
</style>
