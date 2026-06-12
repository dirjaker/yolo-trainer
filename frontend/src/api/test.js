import request from './request'

export const predict = (formData) =>
  request.post('/test/predict', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const batchPredict = (formData) =>
  request.post('/test/batch-predict', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const getResults = (id) => request.get(`/test/results/${id}`)
