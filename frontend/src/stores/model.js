import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getModels as getModelsApi,
  exportModel as exportModelApi,
  deleteModel as deleteModelApi,
} from '../api/model'

export const useModelStore = defineStore('model', () => {
  const models = ref([])
  const total = ref(0)

  async function fetchModels(params) {
    const res = await getModelsApi(params)
    models.value = res.items
    total.value = res.total
  }

  async function exportMdl(id, config) {
    return await exportModelApi(id, config)
  }

  async function deleteMdl(id) {
    return await deleteModelApi(id)
  }

  return { models, total, fetchModels, exportMdl, deleteMdl }
})
