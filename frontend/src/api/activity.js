import request from './request'

export const getActivities = (params) => request.get('/activities', { params })
