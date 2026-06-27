<template>
  <div v-if="model" class="view-wrapper">
    <n-page-header @back="$router.back()">
      <template #title>{{ model.name }}</template>
      <template #extra>
        <n-space>
          <n-tag v-for="t in model.tags" :key="t" size="small">{{ t }}</n-tag>
        </n-space>
      </template>
    </n-page-header>

    <n-grid :cols="3" :x-gap="16" :y-gap="16">
      <n-gi>
        <n-card class="stat-card">
          <n-statistic label="版本" :value="model.version" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card class="stat-card">
          <n-statistic label="大小" :value="formatFileSize(model.file_size)" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card class="stat-card">
          <n-statistic label="创建时间" :value="formatDate(model.created_at)" />
        </n-card>
      </n-gi>
    </n-grid>

    <n-grid :cols="2" :x-gap="16" :y-gap="16">
      <n-gi>
        <n-card title="版本历史" class="section-card">
          <n-timeline v-if="versions.length">
            <n-timeline-item
              v-for="v in versions"
              :key="v.version"
              :title="`v${v.version} (${v.model_version})`"
              :content="v.metrics?.note || v.metrics?.mAP50 ? `mAP50: ${v.metrics.mAP50}` : ''"
              :time="formatDate(v.created_at)"
            />
          </n-timeline>
          <n-empty v-else description="暂无版本历史" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="标签管理" class="section-card">
          <n-dynamic-tags v-model:value="tags" @update:value="handleTags" />
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getModel, addTags, getModelVersions } from '../../api/model'
import { formatDate, formatFileSize } from '../../utils/format'

const route = useRoute()
const model = ref(null)
const versions = ref([])
const tags = ref([])

onMounted(async () => {
  const id = route.params.id
  const [m, v] = await Promise.all([
    getModel(id),
    getModelVersions(id).catch(() => []),
  ])
  model.value = m
  versions.value = v || []
  tags.value = m.tags || []
})

async function handleTags(newTags) {
  await addTags(route.params.id, newTags)
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
