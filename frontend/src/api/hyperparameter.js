import request from './request'

export const createSearch = (config) => request.post('/hyperparameter/searches', config)

export const getSearches = (params) => request.get('/hyperparameter/searches', { params })

export const getSearch = (id) => request.get(`/hyperparameter/searches/${id}`)

export const getTrials = (searchId) =>
  request.get(`/hyperparameter/searches/${searchId}/trials`)
