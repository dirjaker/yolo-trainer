import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard/DashboardView.vue') },
  { path: '/training', name: 'TrainingList', component: () => import('../views/Training/TrainingList.vue') },
  { path: '/training/create', name: 'TrainingCreate', component: () => import('../views/Training/TrainingCreate.vue') },
  { path: '/training/:id', name: 'TrainingDetail', component: () => import('../views/Training/TrainingDetail.vue') },
  { path: '/models', name: 'ModelList', component: () => import('../views/Model/ModelList.vue') },
  { path: '/models/:id', name: 'ModelDetail', component: () => import('../views/Model/ModelDetail.vue') },
  { path: '/datasets', name: 'DatasetList', component: () => import('../views/Dataset/DatasetList.vue') },
  { path: '/test', name: 'Test', component: () => import('../views/Test/TestView.vue') },
  { path: '/compare', name: 'Compare', component: () => import('../views/Compare/CompareView.vue') },
  { path: '/deploy', name: 'Deploy', component: () => import('../views/Deploy/DeployView.vue') },
  { path: '/hyperparameter', name: 'Hyperparameter', component: () => import('../views/Hyperparameter/SearchView.vue') },
  { path: '/team', name: 'Team', component: () => import('../views/Team/TeamView.vue') },
  { path: '/activity', name: 'Activity', component: () => import('../views/Activity/ActivityView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (!to.meta.public && !userStore.token) {
    next('/login')
  } else {
    next()
  }
})

export default router
