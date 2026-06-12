import request from './request'

export const createTeam = (data) => request.post('/teams', data)

export const getTeams = () => request.get('/teams')

export const addMember = (teamId, userId, role) =>
  request.post(`/teams/${teamId}/members`, { user_id: userId, role })

export const removeMember = (teamId, userId) =>
  request.delete(`/teams/${teamId}/members/${userId}`)
