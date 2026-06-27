import request from './request'

export const getModels = (params) => request.get('/models', { params })

export const getModel = (id) => request.get(`/models/${id}`)

export const exportModel = (id, config) => request.post(`/models/${id}/export`, config)

export const deleteModel = (id) => request.delete(`/models/${id}`)

export const addTags = (id, tags) => request.post(`/models/${id}/tags`, { tags })

export const getModelVersions = (id) => request.get(`/models/${id}/versions`)
