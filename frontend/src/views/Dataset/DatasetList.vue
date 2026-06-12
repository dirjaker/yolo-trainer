<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <span />
      <n-upload :action="'#'" :custom-request="handleUpload" :show-file-list="false">
        <n-button type="primary">上传数据集</n-button>
      </n-upload>
    </div>
    <n-data-table :columns="columns" :data="store.datasets" :loading="loading" :bordered="false" />
    <div style="margin-top:16px;display:flex;justify-content:flex-end">
      <n-pagination v-model:page="page" :page-size="pageSize" :item-count="store.total" @update:page="fetchData" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import { NButton, NSpace, useMessage } from 'naive-ui'
import { useDatasetStore } from '../../stores/dataset'
import { formatDate, formatFileSize } from '../../utils/format'

const message = useMessage()
const store = useDatasetStore()
const loading = ref(false)
const page = ref(1)
const pageSize = 20

const columns = [
  { title: '数据集名称', key: 'name' },
  { title: '图片数量', key: 'image_count' },
  { title: '大小', key: 'size', render: (row) => formatFileSize(row.size) },
  { title: '创建时间', key: 'created_at', render: (row) => formatDate(row.created_at) },
  {
    title: '操作',
    key: 'actions',
    render: (row) =>
      h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, { size: 'small', type: 'error', onClick: () => handleDelete(row.id) }, { default: () => '删除' }),
        ],
      }),
  },
]

async function fetchData() {
  loading.value = true
  try { await store.fetchDatasets({ page: page.value, page_size: pageSize }) } finally { loading.value = false }
}

async function handleUpload({ file }) {
  const fd = new FormData()
  fd.append('file', file.file)
  try {
    await store.upload(fd)
    message.success('上传成功')
    fetchData()
  } catch (e) {
    message.error(e?.message || '上传失败')
  }
}

async function handleDelete(id) {
  await store.remove(id)
  fetchData()
}

onMounted(fetchData)
</script>
