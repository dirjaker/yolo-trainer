<template>
  <div class="dashboard">
    <!-- Stat Cards Row -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-icon-circle">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#C7853A" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-label">训练任务总数</span>
          <span class="stat-value">{{ stats.trainingCount }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-circle">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#C7853A" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
            <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
            <line x1="12" y1="22.08" x2="12" y2="12" />
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-label">模型总数</span>
          <span class="stat-value">{{ stats.modelCount }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-circle">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#C7853A" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <ellipse cx="12" cy="5" rx="9" ry="3" />
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-label">数据集总数</span>
          <span class="stat-value">{{ stats.datasetCount }}</span>
        </div>
      </div>
    </div>

    <!-- Table + Chart side by side -->
    <div class="content-row">
      <div class="content-card">
        <div class="card-header">
          <span class="card-header-text">最近训练任务</span>
        </div>
        <n-data-table
          v-if="recentTrainings.length"
          :columns="columns"
          :data="recentTrainings"
          :bordered="false"
          size="small"
        />
        <div v-else class="empty-training-state">
          <div class="empty-icon-circle">
            <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#C7853A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
            </svg>
          </div>
          <p class="empty-title">准备开始训练</p>
          <p class="empty-desc">创建你的第一个训练任务，开启模型优化之旅</p>
          <n-button type="primary" ghost round size="small" @click="$router.push('/training/create')">创建训练</n-button>
        </div>
      </div>
      <div class="content-card">
        <div class="card-header">
          <span class="card-header-text">Loss 曲线</span>
        </div>
        <div ref="lossChart" class="chart-container"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getTrainings } from '../../api/training'
import { getModels } from '../../api/model'
import { getDatasets } from '../../api/dataset'
import { formatDate } from '../../utils/format'

const router = useRouter()
const stats = ref({ trainingCount: 0, modelCount: 0, datasetCount: 0 })
const recentTrainings = ref([])
const lossChart = ref(null)

const columns = [
  { title: '任务名称', key: 'name' },
  { title: '状态', key: 'status' },
  { title: '创建时间', key: 'created_at', render: (row) => formatDate(row.created_at) },
  {
    title: '操作',
    key: 'actions',
    render: (row) =>
      h('n-button', { size: 'small', onClick: () => router.push(`/training/${row.id}`) }, { default: () => '查看' }),
  },
]

import { h } from 'vue'

onMounted(async () => {
  try {
    const [trainingRes, modelRes, datasetRes] = await Promise.all([
      getTrainings({ page: 1, page_size: 5 }),
      getModels({ page: 1, page_size: 1 }),
      getDatasets({ page: 1, page_size: 1 }),
    ])
    stats.value.trainingCount = trainingRes.total || 0
    stats.value.modelCount = modelRes.total || 0
    stats.value.datasetCount = datasetRes.total || 0
    recentTrainings.value = trainingRes.items || []
  } catch {}

  // Simple loss chart
  if (lossChart.value) {
    const chart = echarts.init(lossChart.value)
    chart.setOption({
      xAxis: { type: 'category', data: Array.from({ length: 20 }, (_, i) => `Epoch ${i + 1}`) },
      yAxis: { type: 'value', name: 'Loss' },
      series: [{ data: Array.from({ length: 20 }, (_, i) => (2.5 - i * 0.1 + Math.random() * 0.2).toFixed(3)), type: 'line', smooth: true, itemStyle: { color: '#D4884A' }, areaStyle: { color: 'rgba(212,136,74,0.1)' } }],
      tooltip: { trigger: 'axis' },
    })
  }
})
</script>

<style scoped>
/* ── Design Tokens ──
   primary: #C7853A  |  cards: #FFFFFF  |  border: #EEEBE6
   bg:     #F7F5F0  |  text:   #2D2A26  |  secondary: #A09890
   icon-bg: #FDF6EE
*/

.dashboard {
  padding: 4px 0;
  background: #F7F5F0;
  min-height: 100%;
}

/* ── Stat Cards ── */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  margin-bottom: 24px;
}

.stat-card {
  background: #FFFFFF;
  border: 1px solid #EEEBE6;
  border-radius: 16px;
  padding: 24px 22px;
  display: flex;
  align-items: center;
  gap: 18px;
  transition: transform 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94),
              box-shadow 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(199, 133, 58, 0.08), 0 2px 8px rgba(0, 0, 0, 0.04);
}

.stat-icon-circle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #FDF6EE;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 13px;
  color: #A09890;
  font-weight: 500;
  letter-spacing: 0.01em;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #2D2A26;
  line-height: 1.1;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

/* ── Content Row (table + chart) ── */
.content-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.content-card {
  background: #FFFFFF;
  border: 1px solid #EEEBE6;
  border-radius: 16px;
  padding: 24px 22px;
  transition: box-shadow 0.25s ease;
}

.content-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid #F0EFEC;
}

.card-header-text {
  font-size: 15px;
  font-weight: 600;
  color: #2D2A26;
}

.chart-container {
  height: 300px;
  width: 100%;
}

/* ── Empty Training State ── */
.empty-training-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px 32px;
  text-align: center;
}

.empty-icon-circle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #FDF6EE;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: #2D2A26;
  margin: 0 0 6px;
  line-height: 1.4;
}

.empty-desc {
  font-size: 13px;
  color: #A09890;
  margin: 0 0 20px;
  line-height: 1.5;
}

/* ── Naive UI overrides ── */
.content-card :deep(.n-data-table) {
  --n-td-color: #FFFFFF;
  --n-th-color: #FAF9F7;
  --n-th-font-weight: 600;
  --n-th-text-color: #A09890;
  --n-td-text-color: #2D2A26;
  --n-border-color: #F0EFEC;
}

.content-card :deep(.n-button) {
  --n-color: #C7853A;
  --n-border: #C7853A;
  --n-text-color: #C7853A;
}

.content-card :deep(.n-button:hover) {
  --n-color: rgba(199, 133, 58, 0.08);
}
</style>
