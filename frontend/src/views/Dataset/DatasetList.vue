<template>
  <div class="page-content">
    <div class="page-header">
      <h2 class="page-title">数据集管理</h2>
      <n-upload :action="'#'" :custom-request="handleUpload" :show-file-list="false">
        <n-button type="primary">上传数据集</n-button>
      </n-upload>
    </div>
    <n-card class="content-card" :bordered="true">
      <n-data-table :columns="columns" :data="store.datasets" :loading="loading" :bordered="false">
        <template #empty>
          <n-empty description="暂无数据集" />
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
  { title: '大小', key: 'size', render: (row) => row.stats?.img_size || '-' },
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

.pagination-row {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
