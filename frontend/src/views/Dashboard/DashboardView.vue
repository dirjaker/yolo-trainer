<template>
  <div>
    <n-grid :cols="3" :x-gap="16" :y-gap="16" style="margin-bottom:24px">
      <n-gi>
        <n-card>
          <n-statistic label="训练任务总数" :value="stats.trainingCount" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card>
          <n-statistic label="模型总数" :value="stats.modelCount" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card>
          <n-statistic label="数据集总数" :value="stats.datasetCount" />
        </n-card>
      </n-gi>
    </n-grid>

    <n-grid :cols="2" :x-gap="16">
      <n-gi>
        <n-card title="最近训练任务">
          <n-data-table :columns="columns" :data="recentTrainings" :bordered="false" size="small" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="Loss 曲线">
          <div ref="lossChart" style="height:300px"></div>
        </n-card>
      </n-gi>
    </n-grid>
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
      series: [{ data: Array.from({ length: 20 }, (_, i) => (2.5 - i * 0.1 + Math.random() * 0.2).toFixed(3)), type: 'line', smooth: true }],
      tooltip: { trigger: 'axis' },
    })
  }
})
</script>
