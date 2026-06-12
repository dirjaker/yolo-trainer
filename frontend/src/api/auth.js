import request from './request'

export const login = (username, password) =>
  request.post('/auth/login', { username, password })

export const register = (username, email, password) =>
  request.post('/auth/register', { username, email, password })
