<template>
  <div>
    <n-card title="模型部署">
      <n-grid :cols="2" :x-gap="16">
        <n-gi>
          <n-card title="创建部署" size="small">
            <n-form label-placement="left" label-width="100" :model="form">
              <n-form-item label="选择模型">
                <n-select v-model:value="form.modelId" :options="modelOptions" placeholder="选择模型" />
              </n-form-item>
              <n-form-item label="部署名称">
                <n-input v-model:value="form.name" placeholder="输入部署名称" />
              </n-form-item>
              <n-form-item label="服务类型">
                <n-select v-model:value="form.serviceType" :options="serviceTypeOptions" />
              </n-form-item>
              <n-form-item label="GPU数量">
                <n-input-number v-model:value="form.gpuCount" :min="0" :max="8" />
              </n-form-item>
              <n-form-item label="最大并发">
                <n-input-number v-model:value="form.maxConcurrency" :min="1" :max="100" />
              </n-form-item>
              <n-form-item label="自动扩缩容">
                <n-switch v-model:value="form.autoScale" />
              </n-form-item>
              <n-form-item v-if="form.autoScale" label="最小实例">
                <n-input-number v-model:value="form.minInstances" :min="1" :max="10" />
              </n-form-item>
              <n-form-item v-if="form.autoScale" label="最大实例">
                <n-input-number v-model:value="form.maxInstances" :min="1" :max="20" />
              </n-form-item>
              <n-form-item>
                <n-button type="primary" :loading="deploying" @click="handleDeploy">部署模型</n-button>
              </n-form-item>
            </n-form>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card title="部署说明" size="small">
            <n-alert type="info" style="margin-bottom: 12px">
              部署后将生成 API 端点，可通过 HTTP 请求调用模型推理服务。
            </n-alert>
            <n-descriptions label-placement="left" :column="1" bordered size="small">
              <n-descriptions-item label="服务类型">
                <n-tag type="info">REST API</n-tag> 标准 HTTP 接口
              </n-descriptions-item>
              <n-descriptions-item label="服务类型">
                <n-tag type="success">gRPC</n-tag> 高性能 RPC 接口
              </n-descriptions-item>
              <n-descriptions-item label="服务类型">
                <n-tag type="warning">WebSocket</n-tag> 实时流式接口
              </n-descriptions-item>
            </n-descriptions>
          </n-card>
        </n-gi>
      </n-grid>
    </n-card>

    <n-card title="部署列表" style="margin-top: 16px">
      <n-data-table :columns="columns" :data="deployments" :bordered="false" :loading="loading" />
    </n-card>
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { useMessage, NTag, NButton, NSpace } from 'naive-ui'
import { getModels } from '../../api/model'
import { createDeployment, getDeployments, stopDeployment } from '../../api/deploy'

const message = useMessage()
const loading = ref(false)
const deploying = ref(false)
const modelOptions = ref([])
const deployments = ref([])

const form = ref({
  modelId: null,
  name: '',
  serviceType: 'rest',
  gpuCount: 1,
  maxConcurrency: 10,
  autoScale: false,
  minInstances: 1,
  maxInstances: 5,
})

const serviceTypeOptions = [
  { label: 'REST API', value: 'rest' },
  { label: 'gRPC', value: 'grpc' },
  { label: 'WebSocket', value: 'websocket' },
]

const statusMap = {
  running: { label: '运行中', type: 'success' },
  deploying: { label: '部署中', type: 'warning' },
  stopped: { label: '已停止', type: 'default' },
  failed: { label: '失败', type: 'error' },
}

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '名称', key: 'name' },
  { title: '模型', key: 'model_name' },
  {
    title: '状态', key: 'status', width: 100,
    render: (row) => {
      const s = statusMap[row.status] || { label: row.status, type: 'default' }
      return h(NTag, { type: s.type, size: 'small' }, { default: () => s.label })
    },
  },
  { title: 'API 端点', key: 'endpoint' },
  { title: '创建时间', key: 'created_at' },
  {
    title: '操作', key: 'actions', width: 120,
    render: (row) =>
      h(NSpace, { size: 'small' }, {
        default: () => [
          row.status === 'running'
            ? h(NButton, { size: 'small', type: 'error', onClick: () => handleStop(row.id) }, { default: () => '停止' })
            : null,
        ],
      }),
  },
]

onMounted(async () => {
  try {
    const res = await getModels({ page: 1, page_size: 200 })
    modelOptions.value = (res.items || []).map((m) => ({ label: `${m.name} (${m.version})`, value: m.id }))
  } catch (e) { /* ignore */ }
  loadDeployments()
})

async function loadDeployments() {
  loading.value = true
  try {
    const res = await getDeployments({ page: 1, page_size: 50 })
    deployments.value = res.items || []
  } catch (e) { /* ignore */ }
  loading.value = false
}

async function handleDeploy() {
  if (!form.value.modelId) { message.warning('请选择模型'); return }
  if (!form.value.name) { message.warning('请输入部署名称'); return }
  deploying.value = true
  try {
    await createDeployment(form.value.modelId, {
      name: form.value.name,
      service_type: form.value.serviceType,
      gpu_count: form.value.gpuCount,
      max_concurrency: form.value.maxConcurrency,
      auto_scale: form.value.autoScale,
      min_instances: form.value.minInstances,
      max_instances: form.value.maxInstances,
    })
    message.success('部署任务已创建')
    loadDeployments()
  } catch (e) {
    message.error(e?.message || '部署失败')
  }
  deploying.value = false
}

async function handleStop(id) {
  try {
    await stopDeployment(id)
    message.success('已停止')
    loadDeployments()
  } catch (e) {
    message.error(e?.message || '停止失败')
  }
}
</script>
