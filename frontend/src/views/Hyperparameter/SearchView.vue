<template>
  <div class="view-wrapper">
    <n-grid :cols="2" :x-gap="16" :y-gap="16">
      <n-gi>
        <n-card title="配置搜索空间" class="section-card">
          <n-form label-placement="left" label-width="120" :model="form">
            <n-form-item label="选择训练任务">
              <n-select v-model:value="form.trainingId" :options="trainingOptions" placeholder="选择基础训练任务" />
            </n-form-item>
            <n-form-item label="搜索算法">
              <n-select v-model:value="form.algorithm" :options="algorithmOptions" />
            </n-form-item>
            <n-form-item label="最大试验次数">
              <n-input-number v-model:value="form.maxTrials" :min="5" :max="200" />
            </n-form-item>
            <n-form-item label="优化目标">
              <n-select v-model:value="form.objective" :options="objectiveOptions" />
            </n-form-item>

            <n-divider>搜索参数</n-divider>

            <n-form-item v-for="param in searchParams" :key="param.name" :label="param.label">
              <n-space>
                <n-input-number v-model:value="param.min" :step="param.step" placeholder="最小值" style="width: 120px" />
                <span style="line-height: 34px">~</span>
                <n-input-number v-model:value="param.max" :step="param.step" placeholder="最大值" style="width: 120px" />
                <n-input-number v-model:value="param.step" :min="0.001" placeholder="步长" style="width: 100px" />
              </n-space>
            </n-form-item>

            <n-form-item>
              <n-button type="primary" :loading="creating" @click="handleCreate">开始搜索</n-button>
            </n-form-item>
          </n-form>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="最优参数结果" class="section-card">
          <template v-if="bestTrial">
            <n-descriptions label-placement="left" :column="1" bordered size="small">
              <n-descriptions-item label="最优 mAP">{{ bestTrial.map50?.toFixed(4) }}</n-descriptions-item>
              <n-descriptions-item v-for="p in bestTrial.params" :key="p.name" :label="p.name">
                {{ p.value }}
              </n-descriptions-item>
            </n-descriptions>
          </template>
          <n-empty v-else description="运行搜索后查看最优参数" />
        </n-card>

        <n-card title="搜索进度" class="section-card" style="margin-top: 16px">
          <template v-if="currentSearch">
            <n-progress
              type="line"
              :percentage="Math.round((currentSearch.completed_trials / currentSearch.max_trials) * 100)"
              :indicator-placement="'inside'"
            />
            <n-descriptions label-placement="left" :column="2" bordered size="small" style="margin-top: 12px">
              <n-descriptions-item label="已完成">{{ currentSearch.completed_trials }} / {{ currentSearch.max_trials }}</n-descriptions-item>
              <n-descriptions-item label="状态">
                <n-tag :type="currentSearch.status === 'running' ? 'warning' : 'success'" size="small">
                  {{ currentSearch.status === 'running' ? '搜索中' : '已完成' }}
                </n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="当前最优 mAP">{{ currentSearch.best_map?.toFixed(4) }}</n-descriptions-item>
              <n-descriptions-item label="耗时">{{ currentSearch.elapsed }}</n-descriptions-item>
            </n-descriptions>
          </template>
          <n-empty v-else description="暂无进行中的搜索" />
        </n-card>
      </n-gi>
    </n-grid>

    <n-card title="试验列表" class="section-card">
      <n-data-table :columns="trialColumns" :data="trials" :bordered="false" :loading="trialsLoading" />
    </n-card>

    <n-card title="搜索历史" class="section-card">
      <n-data-table :columns="historyColumns" :data="searchHistory" :bordered="false" :loading="historyLoading" />
    </n-card>
  </div>
</template>

<script setup>
import { ref, h, onMounted, onUnmounted } from 'vue'
import { useMessage, NTag, NButton } from 'naive-ui'
import { getModels } from '../../api/model'
import { createSearch, getSearches, getSearch, getTrials } from '../../api/hyperparameter'

const message = useMessage()
const creating = ref(false)
const trialsLoading = ref(false)
const historyLoading = ref(false)

const form = ref({
  trainingId: null,
  algorithm: 'bayesian',
  maxTrials: 20,
  objective: 'map50',
})

const searchParams = ref([
  { name: 'lr', label: '学习率', min: 0.0001, max: 0.1, step: 0.0001 },
  { name: 'batch_size', label: 'Batch Size', min: 4, max: 64, step: 4 },
  { name: 'momentum', label: '动量', min: 0.8, max: 0.99, step: 0.01 },
  { name: 'weight_decay', label: '权重衰减', min: 0.0001, max: 0.01, step: 0.0001 },
])

const trainingOptions = ref([])
const algorithmOptions = [
  { label: '贝叶斯优化', value: 'bayesian' },
  { label: '随机搜索', value: 'random' },
  { label: '网格搜索', value: 'grid' },
]
const objectiveOptions = [
  { label: 'mAP@0.5', value: 'map50' },
  { label: 'mAP@0.5:0.95', value: 'map50_95' },
  { label: '推理速度', value: 'inference_time' },
]

const bestTrial = ref(null)
const currentSearch = ref(null)
const trials = ref([])
const searchHistory = ref([])

let pollTimer = null

const trialColumns = [
  { title: '试验ID', key: 'id', width: 80 },
  { title: '学习率', key: 'lr', render: (r) => r.params?.lr?.toFixed(6) },
  { title: 'Batch Size', key: 'batch_size', render: (r) => r.params?.batch_size },
  { title: '动量', key: 'momentum', render: (r) => r.params?.momentum?.toFixed(4) },
  { title: 'mAP@0.5', key: 'map50', render: (r) => r.map50?.toFixed(4) },
  {
    title: '状态', key: 'status', width: 80,
    render: (row) => h(NTag, { type: row.status === 'completed' ? 'success' : 'warning', size: 'small' }, { default: () => row.status }),
  },
]

const historyColumns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '算法', key: 'algorithm' },
  { title: '试验次数', key: 'max_trials' },
  { title: '最优mAP', key: 'best_map', render: (r) => r.best_map?.toFixed(4) },
  { title: '创建时间', key: 'created_at' },
  {
    title: '操作', key: 'actions', width: 100,
    render: (row) => h(NButton, { size: 'small', onClick: () => loadSearch(row.id) }, { default: () => '查看' }),
  },
]

onMounted(async () => {
  try {
    const res = await getModels({ page: 1, page_size: 200 })
    trainingOptions.value = (res.items || []).map((m) => ({ label: `${m.name} (${m.version})`, value: m.id }))
  } catch (e) { /* ignore */ }
  loadHistory()
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

async function loadHistory() {
  historyLoading.value = true
  try {
    const res = await getSearches({ page: 1, page_size: 20 })
    searchHistory.value = res.items || []
  } catch (e) { /* ignore */ }
  historyLoading.value = false
}

async function handleCreate() {
  creating.value = true
  try {
    const res = await createSearch({
      training_id: form.value.trainingId,
      algorithm: form.value.algorithm,
      max_trials: form.value.maxTrials,
      objective: form.value.objective,
      search_space: searchParams.value.map((p) => ({
        name: p.name, min: p.min, max: p.max, step: p.step,
      })),
    })
    currentSearch.value = res
    message.success('搜索任务已创建')
    startPolling(res.id)
    loadHistory()
  } catch (e) {
    message.error(e?.message || '创建失败')
  }
  creating.value = false
}

async function loadSearch(id) {
  try {
    const res = await getSearch(id)
    currentSearch.value = res
    bestTrial.value = res.best_trial || null
    const trialRes = await getTrials(id)
    trials.value = trialRes.items || []
  } catch (e) { /* ignore */ }
}

function startPolling(id) {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    try {
      const res = await getSearch(id)
      currentSearch.value = res
      bestTrial.value = res.best_trial || null
      const trialRes = await getTrials(id)
      trials.value = trialRes.items || []
      if (res.status !== 'running') {
        clearInterval(pollTimer)
        pollTimer = null
      }
    } catch (e) { /* ignore */ }
  }, 5000)
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
