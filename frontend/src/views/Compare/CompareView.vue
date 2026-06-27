<template>
  <div class="view-wrapper">
    <n-card title="模型对比" class="section-card">
      <n-space vertical :size="16">
        <n-space align="center">
          <n-select
            v-model:value="selectedModels"
            :options="modelOptions"
            multiple
            placeholder="选择要对比的模型（最多5个）"
            style="min-width: 400px"
            :max-tag-count="3"
          />
          <n-select
            v-model:value="testDatasetId"
            :options="datasetOptions"
            placeholder="选择测试数据集"
            style="min-width: 200px"
          />
          <n-button type="primary" :loading="loading" :disabled="selectedModels.length < 2" @click="runCompare">
            开始对比
          </n-button>
        </n-space>

        <n-spin :show="loading">
          <template v-if="compareResult">
            <n-grid :cols="3" :x-gap="16" :y-gap="16">
              <n-gi>
                <n-card size="small" title="mAP@0.5" class="chart-card">
                  <div ref="mapChartRef" style="height: 300px"></div>
                </n-card>
              </n-gi>
              <n-gi>
                <n-card size="small" title="推理速度 (ms)" class="chart-card">
                  <div ref="speedChartRef" style="height: 300px"></div>
                </n-card>
              </n-gi>
              <n-gi>
                <n-card size="small" title="模型大小 (MB)" class="chart-card">
                  <div ref="sizeChartRef" style="height: 300px"></div>
                </n-card>
              </n-gi>
            </n-grid>

            <n-card title="详细对比数据" size="small" class="section-card">
              <n-data-table :columns="detailColumns" :data="compareResult.details" :bordered="false" />
            </n-card>
          </template>
          <n-empty v-else description="选择模型和数据集后开始对比" />
        </n-spin>
      </n-space>
    </n-card>

    <n-card title="历史对比记录" class="section-card">
      <n-data-table :columns="historyColumns" :data="historyList" :bordered="false" :loading="historyLoading" />
    </n-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useMessage } from 'naive-ui'
import * as echarts from 'echarts'
import { getModels } from '../../api/model'
import { createCompare, getCompare, getCompares } from '../../api/compare'

const message = useMessage()
const loading = ref(false)
const historyLoading = ref(false)
const selectedModels = ref([])
const testDatasetId = ref(null)
const modelOptions = ref([])
const datasetOptions = ref([])
const compareResult = ref(null)
const historyList = ref([])

const mapChartRef = ref(null)
const speedChartRef = ref(null)
const sizeChartRef = ref(null)

const detailColumns = [
  { title: '模型', key: 'model_name' },
  { title: 'mAP@0.5', key: 'map50', render: (r) => r.map50?.toFixed(4) },
  { title: 'mAP@0.5:0.95', key: 'map50_95', render: (r) => r.map50_95?.toFixed(4) },
  { title: '推理速度 (ms)', key: 'inference_time', render: (r) => r.inference_time?.toFixed(1) },
  { title: '模型大小 (MB)', key: 'model_size', render: (r) => r.model_size?.toFixed(1) },
  { title: '参数量 (M)', key: 'params', render: (r) => r.params?.toFixed(2) },
]

const historyColumns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '对比模型', key: 'model_names' },
  { title: '测试数据集', key: 'dataset_name' },
  { title: '创建时间', key: 'created_at' },
  {
    title: '操作', key: 'actions', width: 100,
    render: (row) => h('n-button', { size: 'small', onClick: () => loadCompare(row.id) }, { default: () => '查看' })
  },
]

import { h } from 'vue'

onMounted(async () => {
  try {
    const res = await getModels({ page: 1, page_size: 200 })
    modelOptions.value = (res.items || []).map((m) => ({ label: `${m.name} (${m.version})`, value: m.id }))
  } catch (e) { /* ignore */ }
  loadHistory()
})

async function loadHistory() {
  historyLoading.value = true
  try {
    const res = await getCompares({ page: 1, page_size: 20 })
    historyList.value = res.items || []
  } catch (e) { /* ignore */ }
  historyLoading.value = false
}

async function runCompare() {
  if (selectedModels.value.length < 2) return
  loading.value = true
  try {
    const res = await createCompare(selectedModels.value, testDatasetId.value)
    compareResult.value = res
    await nextTick()
    renderCharts(res)
    message.success('对比完成')
    loadHistory()
  } catch (e) {
    message.error(e?.message || '对比失败')
  }
  loading.value = false
}

async function loadCompare(id) {
  loading.value = true
  try {
    const res = await getCompare(id)
    compareResult.value = res
    await nextTick()
    renderCharts(res)
  } catch (e) {
    message.error(e?.message || '加载失败')
  }
  loading.value = false
}

function renderCharts(data) {
  const names = data.details.map((d) => d.model_name)
  const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']

  const makeBar = (ref, values, unit) => {
    if (!ref.value) return
    const chart = echarts.init(ref.value)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: names, axisLabel: { rotate: 30 } },
      yAxis: { type: 'value', name: unit },
      series: [{ type: 'bar', data: values, itemStyle: { color: (p) => colors[p.dataIndex % colors.length] } }],
    })
  }

  makeBar(mapChartRef, data.details.map((d) => d.map50), '')
  makeBar(speedChartRef, data.details.map((d) => d.inference_time), 'ms')
  makeBar(sizeChartRef, data.details.map((d) => d.model_size), 'MB')
}
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
