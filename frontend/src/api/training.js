import request from './request'

export const createTraining = (data) => request.post('/trainings', data)

export const getTrainings = (params) => request.get('/trainings', { params })

export const getTraining = (id) => request.get(`/trainings/${id}`)

export const stopTraining = (id) => request.post(`/trainings/${id}/stop`)

export const getTrainingMetrics = (id) => request.get(`/trainings/${id}/metrics`)
