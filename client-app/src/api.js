import axios from 'axios'

// Vite exposes env vars as import.meta.env.VITE_*
const BASE = import.meta.env?.VITE_API_URL || '/'
const api = axios.create({ baseURL: BASE })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const login = async (username, password) => {
  const { data } = await axios.post(`${BASE}login`, { username, password })
  localStorage.setItem('token', data.access_token)
  localStorage.setItem('username', username)
  return data
}

export const registerUser = (username, password, email) =>
  axios.post('/register', { username, password, email })

export const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
}

export const verifyUser = (username, email) =>
  api.get('/users/verify', { params: { username, email } }).then((r) => r.data)

export const getMessages = () => api.get('/messages').then((r) => r.data)

export const sendMessage = (recipient, content) =>
  api.post('/messages', { recipient, content }).then((r) => r.data)

export const getMyGroups = () => api.get('/groups/my').then((r) => r.data)

export const getAllGroups = () => api.get('/groups').then((r) => r.data)

export const getGroupMessages = (groupId) =>
  api.get(`/groups/${groupId}/messages`).then((r) => r.data)

export const createGroup = (name, join_password) =>
  api.post('/groups', { name, join_password }).then((r) => r.data)

export const joinGroup = (groupId, password, message) =>
  api.post(`/groups/${groupId}/join`, { password, message }).then((r) => r.data)

export const getJoinRequests = (groupId) =>
  api.get(`/groups/${groupId}/join-requests`).then((r) => r.data)

export const approveRequest = (groupId, requestId) =>
  api.post(`/groups/${groupId}/join-requests/${requestId}/approve`).then((r) => r.data)

export const rejectRequest = (groupId, requestId) =>
  api.post(`/groups/${groupId}/join-requests/${requestId}/reject`).then((r) => r.data)

export const sendGroupMessage = (groupId, content) =>
  api.post(`/groups/${groupId}/messages`, { content }).then((r) => r.data)
