import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getDatasets as getDatasetsApi,
  uploadDataset as uploadDatasetApi,
  deleteDataset as deleteDatasetApi,
} from '../api/dataset'

export const useDatasetStore = defineStore('dataset', () => {
  const datasets = ref([])
  const total = ref(0)

  async function fetchDatasets(params) {
    const res = await getDatasetsApi(params)
    datasets.value = res.items
    total.value = res.total
  }

  async function upload(formData, onProgress) {
    return await uploadDatasetApi(formData)
  }

  async function remove(id) {
    return await deleteDatasetApi(id)
  }

  return { datasets, total, fetchDatasets, upload, remove }
})
