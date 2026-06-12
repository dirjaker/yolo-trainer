import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getTrainings as getTrainingsApi,
  createTraining as createTrainingApi,
  stopTraining as stopTrainingApi,
  getTrainingMetrics as getTrainingMetricsApi,
} from '../api/training'

export const useTrainingStore = defineStore('training', () => {
  const trainings = ref([])
  const total = ref(0)
  const current = ref(null)
  const metrics = ref(null)

  async function fetchTrainings(params) {
    const res = await getTrainingsApi(params)
    trainings.value = res.items
    total.value = res.total
  }

  async function createTraining(data) {
    return await createTrainingApi(data)
  }

  async function stopTraining(id) {
    return await stopTrainingApi(id)
  }

  async function fetchMetrics(id) {
    metrics.value = await getTrainingMetricsApi(id)
  }

  return { trainings, total, current, metrics, fetchTrainings, createTraining, stopTraining, fetchMetrics }
})
