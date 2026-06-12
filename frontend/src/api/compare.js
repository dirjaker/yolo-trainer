import request from './request'

export const createCompare = (modelIds, testDatasetId) =>
  request.post('/compares', { model_ids: modelIds, test_dataset_id: testDatasetId })

export const getCompare = (id) => request.get(`/compares/${id}`)

export const getCompares = (params) => request.get('/compares', { params })
