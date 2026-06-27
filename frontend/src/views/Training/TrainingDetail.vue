<template>
  <div v-if="training" class="view-wrapper">
    <n-page-header @back="$router.back()">
      <template #title>{{ training.name }}</template>
      <template #extra>
        <n-tag :type="statusTypeMap[training.status]">{{ training.status }}</n-tag>
      </template>
    </n-page-header>

    <n-grid :cols="4" :x-gap="16" :y-gap="16">
      <n-gi>
        <n-card class="stat-card">
          <n-statistic label="进度" :value="`${Math.round(training.progress || 0)}%`" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card class="stat-card">
          <n-statistic label="Epochs" :value="`${training.config?.epochs || '-'}`" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card class="stat-card">
          <n-statistic label="mAP50" :value="training.metrics?.mAP50 || '-'" :precision="4" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card class="stat-card">
          <n-statistic label="F1" :value="training.metrics?.F1 || '-'" :precision="4" />
        </n-card>
      </n-gi>
    </n-grid>

    <n-grid :cols="2" :x-gap="16" :y-gap="16">
      <n-gi>
        <n-card title="Loss / mAP 曲线" class="section-card">
          <div ref="chartRef" style="height:350px"></div>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="训练日志" class="section-card">
          <n-log v-if="logs" :log="logs" :rows="16" />
          <n-empty v-else description="暂无日志" />
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { getTraining, getTrainingMetrics } from '../../api/training'

const route = useRoute()
const training = ref(null)
const logs = ref('')
const chartRef = ref(null)
let chart = null
let timer = null

const statusTypeMap = { pending: 'info', running: 'warning', completed: 'success', failed: 'error', stopped: 'default' }

async function load() {
  training.value = await getTraining(route.params.id)
  try {
    const m = await getTrainingMetrics(route.params.id)
    if (m && chartRef.value && m.epochs?.length) {
      if (!chart) chart = echarts.init(chartRef.value)
      chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['Loss', 'mAP50'] },
        xAxis: { type: 'category', data: m.epochs.map((e) => `E${e}`) },
        yAxis: [{ type: 'value', name: 'Loss' }, { type: 'value', name: 'mAP50', position: 'right', min: 0, max: 1 }],
        series: [
          { name: 'Loss', type: 'line', data: m.loss || [], smooth: true, symbol: 'none' },
          { name: 'mAP50', type: 'line', yAxisIndex: 1, data: m.map || [], smooth: true, symbol: 'none' },
        ],
      })
    }
    if (m?.logs) logs.value = m.logs
  } catch {}
}

onMounted(() => {
  load()
  timer = setInterval(load, 5000)
})

onUnmounted(() => {
  clearInterval(timer)
  chart?.dispose()
})
</script>

<style scoped>
.view-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.view-wrapper :deep(.n-card) {
  border-radius: 14px;
}
</style>
