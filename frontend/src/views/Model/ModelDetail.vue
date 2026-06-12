<template>
  <div v-if="model">
    <n-page-header @back="$router.back()">
      <template #title>{{ model.name }}</template>
      <template #extra>
        <n-space>
          <n-tag v-for="t in model.tags" :key="t" size="small">{{ t }}</n-tag>
        </n-space>
      </template>
    </n-page-header>

    <n-grid :cols="3" :x-gap="16" style="margin:16px 0">
      <n-gi><n-card><n-statistic label="版本" :value="model.version" /></n-card></n-gi>
      <n-gi><n-card><n-statistic label="大小" :value="formatFileSize(model.size)" /></n-card></n-gi>
      <n-gi><n-card><n-statistic label="创建时间" :value="formatDate(model.created_at)" /></n-card></n-gi>
    </n-grid>

    <n-grid :cols="2" :x-gap="16">
      <n-gi>
        <n-card title="版本历史">
          <n-timeline>
            <n-timeline-item v-for="v in model.history" :key="v.version" :title="v.version" :content="v.description" :time="formatDate(v.created_at)" />
          </n-timeline>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="标签管理">
          <n-dynamic-tags v-model:value="tags" @update:value="handleTags" />
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getModel, addTags } from '../../api/model'
import { formatDate, formatFileSize } from '../../utils/format'

const route = useRoute()
const model = ref(null)
const tags = ref([])

onMounted(async () => {
  model.value = await getModel(route.params.id)
  tags.value = model.value.tags || []
})

async function handleTags(newTags) {
  await addTags(route.params.id, newTags)
}
</script>
