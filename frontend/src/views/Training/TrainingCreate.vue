<template>
  <div class="view-wrapper">
    <n-card title="创建训练任务" class="section-card">
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="120">
        <n-form-item label="任务名称" path="name">
          <n-input v-model:value="form.name" placeholder="输入任务名称" />
        </n-form-item>
        <n-form-item label="模型版本" path="model_version">
          <n-select v-model:value="form.model_version" :options="modelVersions" placeholder="选择模型版本" />
        </n-form-item>
        <n-form-item label="数据集" path="dataset_id">
          <n-select v-model:value="form.dataset_id" :options="datasets" placeholder="选择数据集" />
        </n-form-item>
        <n-form-item label="Epochs" path="epochs">
          <n-input-number v-model:value="form.epochs" :min="1" :max="1000" />
        </n-form-item>
        <n-form-item label="Batch Size" path="batch_size">
          <n-input-number v-model:value="form.batch_size" :min="1" :max="256" />
        </n-form-item>
        <n-form-item label="学习率" path="learning_rate">
          <n-input-number v-model:value="form.learning_rate" :min="0.00001" :max="1" :step="0.0001" />
        </n-form-item>
        <n-form-item label="图像尺寸" path="img_size">
          <n-select v-model:value="form.img_size" :options="[{label:'640',value:640},{label:'1280',value:1280},{label:'416',value:416}]" />
        </n-form-item>
        <n-form-item>
          <n-space>
            <n-button type="primary" :loading="loading" @click="handleSubmit">开始训练</n-button>
            <n-button @click="$router.back()">取消</n-button>
          </n-space>
        </n-form-item>
      </n-form>
    </n-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useTrainingStore } from '../../stores/training'
import { getModels } from '../../api/model'
import { getDatasets } from '../../api/dataset'

const router = useRouter()
const message = useMessage()
const store = useTrainingStore()
const formRef = ref(null)
const loading = ref(false)
const modelVersions = ref([])
const datasets = ref([])

const form = ref({
  name: '',
  model_version: null,
  dataset_id: null,
  epochs: 100,
  batch_size: 16,
  learning_rate: 0.01,
  img_size: 640,
})

const rules = {
  name: { required: true, message: '请输入任务名称' },
  model_version: { required: true, message: '请选择模型版本' },
  dataset_id: { required: true, message: '请选择数据集' },
}

onMounted(async () => {
  const [mRes, dRes] = await Promise.all([getModels({ page: 1, page_size: 100 }), getDatasets({ page: 1, page_size: 100 })])
  modelVersions.value = (mRes.items || []).map((m) => ({ label: m.name, value: m.model_version }))
  datasets.value = (dRes.items || []).map((d) => ({ label: d.name, value: d.id }))
})

async function handleSubmit() {
  try {
    loading.value = true
    const payload = {
      name: form.value.name,
      model_version: form.value.model_version,
      dataset_id: form.value.dataset_id,
      config: {
        epochs: form.value.epochs,
        batch: form.value.batch_size,
        lr0: form.value.learning_rate,
        imgsz: form.value.img_size,
      },
    }
    await store.createTraining(payload)
    message.success('训练任务已创建')
    router.push('/training')
  } catch (e) {
    message.error(e?.message || '创建失败')
  } finally {
    loading.value = false
  }
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
