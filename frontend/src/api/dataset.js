import request from './request'

export const uploadDataset = (formData) =>
  request.post('/datasets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const getDatasets = (params) => request.get('/datasets', { params })

export const getDataset = (id) => request.get(`/datasets/${id}`)

export const deleteDataset = (id) => request.delete(`/datasets/${id}`)
