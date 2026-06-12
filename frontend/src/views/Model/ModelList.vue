<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <n-space>
        <n-select v-model:value="filter.version" :options="versionOptions" placeholder="版本筛选" clearable style="width:160px" @update:value="fetchData" />
      </n-space>
    </div>
    <n-data-table :columns="columns" :data="store.models" :loading="loading" :bordered="false" />
    <div style="margin-top:16px;display:flex;justify-content:flex-end">
      <n-pagination v-model:page="page" :page-size="pageSize" :item-count="store.total" @update:page="fetchData" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NSpace, NTag } from 'naive-ui'
import { useModelStore } from '../../stores/model'
import { formatDate, formatFileSize } from '../../utils/format'

const router = useRouter()
const store = useModelStore()
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const filter = ref({ version: null })
const versionOptions = [
  { label: 'YOLOv8n', value: 'yolov8n' },
  { label: 'YOLOv8s', value: 'yolov8s' },
  { label: 'YOLOv8m', value: 'yolov8m' },
  { label: 'YOLOv8l', value: 'yolov8l' },
  { label: 'YOLOv8x', value: 'yolov8x' },
]

const columns = [
  { title: '模型名称', key: 'name' },
  { title: '版本', key: 'version' },
  { title: '大小', key: 'size', render: (row) => formatFileSize(row.size) },
  { title: '标签', key: 'tags', render: (row) => (row.tags || []).map((t) => h(NTag, { size: 'small', style: 'margin-right:4px' }, { default: () => t })) },
  { title: '创建时间', key: 'created_at', render: (row) => formatDate(row.created_at) },
  {
    title: '操作',
    key: 'actions',
    render: (row) =>
      h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, { size: 'small', onClick: () => router.push(`/models/${row.id}`) }, { default: () => '查看' }),
          h(NButton, { size: 'small', type: 'warning', onClick: () => handleExport(row.id) }, { default: () => '导出' }),
          h(NButton, { size: 'small', type: 'error', onClick: () => handleDelete(row.id) }, { default: () => '删除' }),
        ],
      }),
  },
]

async function fetchData() {
  loading.value = true
  try { await store.fetchModels({ page: page.value, page_size: pageSize, ...filter.value }) } finally { loading.value = false }
}

async function handleExport(id) {
  await store.exportMdl(id, { format: 'onnx' })
}

async function handleDelete(id) {
  await store.deleteMdl(id)
  fetchData()
}

onMounted(fetchData)
</script>
