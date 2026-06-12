import request from './request'

export const createDeployment = (modelId, config) =>
  request.post('/deployments', { model_id: modelId, ...config })

export const getDeployments = (params) => request.get('/deployments', { params })

export const getDeployment = (id) => request.get(`/deployments/${id}`)

export const stopDeployment = (id) => request.post(`/deployments/${id}/stop`)
