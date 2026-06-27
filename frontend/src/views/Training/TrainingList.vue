<template>
  <div class="page-content">
    <div class="page-header">
      <h2 class="page-title">训练任务</h2>
      <n-button type="primary" @click="$router.push('/training/create')">创建训练</n-button>
    </div>
    <n-card class="content-card" :bordered="true">
      <div class="filter-row">
        <n-select v-model:value="filter.status" :options="statusOptions" placeholder="状态筛选" clearable style="width:200px" @update:value="fetchData" />
      </div>
      <n-data-table :columns="columns" :data="store.trainings" :loading="loading" :bordered="false">
        <template #empty>
          <n-empty description="暂无训练任务" />
        </template>
      </n-data-table>
      <div class="pagination-row">
        <n-pagination v-model:page="page" :page-size="pageSize" :item-count="store.total" @update:page="fetchData" />
      </div>
    </n-card>
  </div>
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NSpace, NTag } from 'naive-ui'
import { useTrainingStore } from '../../stores/training'
import { formatDate } from '../../utils/format'

const router = useRouter()
const store = useTrainingStore()
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const filter = ref({ status: null })

const statusOptions = [
  { label: '等待中', value: 'pending' },
  { label: '训练中', value: 'running' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' },
  { label: '已停止', value: 'stopped' },
]

const statusTypeMap = { pending: 'info', running: 'warning', completed: 'success', failed: 'error', stopped: 'default' }

const columns = [
  { title: '任务名称', key: 'name' },
  { title: '模型版本', key: 'model_version' },
  { title: '状态', key: 'status', render: (row) => h(NTag, { type: statusTypeMap[row.status] || 'default', size: 'small' }, { default: () => row.status }) },
  { title: 'Epochs', key: 'epochs' },
  { title: '创建时间', key: 'created_at', render: (row) => formatDate(row.created_at) },
  {
    title: '操作',
    key: 'actions',
    render: (row) =>
      h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, { size: 'small', onClick: () => router.push(`/training/${row.id}`) }, { default: () => '查看' }),
          row.status === 'running'
            ? h(NButton, { size: 'small', type: 'error', onClick: () => handleStop(row.id) }, { default: () => '停止' })
            : null,
        ],
      }),
  },
]

async function fetchData() {
  loading.value = true
  try {
    await store.fetchTrainings({ page: page.value, page_size: pageSize, ...filter.value })
  } finally {
    loading.value = false
  }
}

async function handleStop(id) {
  await store.stopTraining(id)
  fetchData()
}

onMounted(fetchData)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #1F2937;
  margin: 0;
}

.content-card {
  border-radius: 14px;
  background: #FFFFFF;
}

.content-card :deep(.n-card) {
  border-radius: 14px;
  border-color: #F0EFEC;
}

.filter-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.pagination-row {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
