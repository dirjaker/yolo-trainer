<template>
  <div class="view-wrapper">
    <n-grid :cols="2" :x-gap="16" :y-gap="16" responsive="screen">
      <n-gi>
        <n-card title="上传图片进行检测" class="section-card">
          <n-form label-placement="left" label-width="100">
            <n-form-item label="选择模型">
              <n-select v-model:value="modelId" :options="modelOptions" placeholder="选择模型" />
            </n-form-item>
            <n-form-item label="置信度">
              <n-slider v-model:value="conf" :min="0.1" :max="1" :step="0.05" />
            </n-form-item>
            <n-form-item label="上传图片">
              <n-upload :action="'#'" :custom-request="handlePredict" :show-file-list="false" accept="image/*">
                <n-button type="primary">选择图片</n-button>
              </n-upload>
            </n-form-item>
          </n-form>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="检测结果" class="section-card">
          <div v-if="resultImage" style="text-align:center">
            <img :src="resultImage" style="max-width:100%;border-radius:8px" />
          </div>
          <div v-if="detections.length" style="margin-top:16px">
            <n-data-table :columns="detColumns" :data="detections" :bordered="false" size="small" />
          </div>
          <n-empty v-if="!resultImage" description="上传图片后查看检测结果" />
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { getModels } from '../../api/model'
import { predict } from '../../api/test'

const message = useMessage()
const modelId = ref(null)
const conf = ref(0.25)
const modelOptions = ref([])
const resultImage = ref('')
const detections = ref([])

const detColumns = [
  { title: '类别', key: 'class' },
  { title: '置信度', key: 'confidence', render: (row) => (row.confidence * 100).toFixed(1) + '%' },
  { title: '位置', key: 'bbox', render: (row) => `[${row.bbox.map((v) => Math.round(v)).join(', ')}]` },
]

onMounted(async () => {
  const res = await getModels({ page: 1, page_size: 100 })
  modelOptions.value = (res.items || []).map((m) => ({ label: `${m.name} (${m.version})`, value: m.id }))
})

async function handlePredict({ file }) {
  if (!modelId.value) {
    message.warning('请先选择模型')
    return
  }
  const fd = new FormData()
  fd.append('file', file.file)
  fd.append('model_id', modelId.value)
  fd.append('conf', conf.value)
  try {
    const res = await predict(fd)
    resultImage.value = res.image_url
    detections.value = res.detections || []
  } catch (e) {
    message.error(e?.message || '检测失败')
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
