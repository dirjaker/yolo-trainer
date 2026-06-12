<template>
  <div>
    <n-card title="活动日志">
      <template #header-extra>
        <n-space>
          <n-select
            v-model:value="filters.user"
            :options="userOptions"
            placeholder="筛选用户"
            clearable
            style="width: 160px"
          />
          <n-select
            v-model:value="filters.type"
            :options="typeOptions"
            placeholder="筛选类型"
            clearable
            style="width: 160px"
          />
          <n-date-picker
            v-model:value="filters.dateRange"
            type="daterange"
            clearable
            style="width: 280px"
          />
          <n-button type="primary" @click="loadActivities">查询</n-button>
        </n-space>
      </template>

      <n-timeline>
        <n-timeline-item
          v-for="activity in activities"
          :key="activity.id"
          :type="getTimelineType(activity.type)"
          :title="activity.title"
          :content="activity.content"
          :time="activity.created_at"
        />
      </n-timeline>
      <n-empty v-if="!activities.length && !loading" description="暂无活动记录" />

      <div style="margin-top: 16px; text-align: center">
        <n-pagination
          v-model:page="pagination.page"
          :page-count="pagination.pageCount"
          @update:page="loadActivities"
        />
      </div>
    </n-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getActivities } from '../../api/activity'

const loading = ref(false)
const activities = ref([])

const filters = ref({
  user: null,
  type: null,
  dateRange: null,
})

const pagination = ref({ page: 1, pageCount: 1 })

const userOptions = ref([])
const typeOptions = [
  { label: '训练', value: 'training' },
  { label: '模型', value: 'model' },
  { label: '数据集', value: 'dataset' },
  { label: '部署', value: 'deploy' },
  { label: '测试', value: 'test' },
  { label: '团队', value: 'team' },
]

const typeColorMap = {
  training: 'info',
  model: 'success',
  dataset: 'warning',
  deploy: 'error',
  test: 'info',
  team: 'default',
}

function getTimelineType(type) {
  return typeColorMap[type] || 'default'
}

onMounted(loadActivities)

async function loadActivities() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: 20,
    }
    if (filters.value.user) params.user = filters.value.user
    if (filters.value.type) params.type = filters.value.type
    if (filters.value.dateRange) {
      params.start_date = filters.value.dateRange[0]
      params.end_date = filters.value.dateRange[1]
    }
    const res = await getActivities(params)
    activities.value = res.items || []
    pagination.value.pageCount = Math.ceil((res.total || 0) / 20)
  } catch (e) { /* ignore */ }
  loading.value = false
}
</script>
