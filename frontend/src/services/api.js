import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('institack_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('institack_token')
      localStorage.removeItem('institack_user')
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api

// Auth
export const login = (username, password) => {
  const form = new URLSearchParams()
  form.append('username', username)
  form.append('password', password)
  return api.post('/api/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
}
export const register = (data) => api.post('/api/auth/register', data)
export const getMe = () => api.get('/api/auth/me')

// Cases
export const submitCase = (data) => api.post('/api/cases', data)
export const listCases = (params) => api.get('/api/cases', { params })
export const getCase = (id) => api.get(`/api/cases/${id}`)
export const acceptCase = (id, data = {}) => api.post(`/api/cases/${id}/accept`, data)
export const rejectCase = (id, data) => api.post(`/api/cases/${id}/reject`, data)
export const requestInfo = (id, data) => api.post(`/api/cases/${id}/request-information`, data)
export const respondInfo = (id, data) => api.post(`/api/cases/${id}/respond-information`, data)
export const assignCase = (id, data) => api.post(`/api/cases/${id}/assign`, data)
export const acknowledgeAssignment = (id) => api.post(`/api/cases/${id}/acknowledge-assignment`)
export const updateStatus = (id, data) => api.post(`/api/cases/${id}/status`, data)
export const submitResolution = (id, data) => api.post(`/api/cases/${id}/submit-resolution`, data)
export const approveClosure = (id, data) => api.post(`/api/cases/${id}/approve-closure`, data)
export const getRelated = (id) => api.get(`/api/cases/${id}/related`)
export const confirmRelated = (id, targetId, confirmed = true) =>
  api.post(`/api/cases/${id}/related/${targetId}/confirm`, null, { params: { confirmed } })
export const addComment = (id, content, isInternal = true) => {
  const form = new FormData()
  form.append('content', content)
  form.append('is_internal', isInternal)
  return api.post(`/api/cases/${id}/comments`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
}
export const uploadAttachment = (id, file, isEvidence = false, isPublic = false) => {
  const form = new FormData()
  form.append('file', file)
  form.append('is_evidence', isEvidence)
  form.append('is_public_to_complainant', isPublic)
  return api.post(`/api/cases/${id}/attachments`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
}

// Institutions
export const listInstitutions = (params) => api.get('/api/institutions', { params })
export const listInstitutionsPublic = (params) => api.get('/api/institutions/public', { params })
export const getInstitution = (id) => api.get(`/api/institutions/${id}`)
export const getInstitutionStats = (id) => api.get(`/api/institutions/${id}/stats`)

// Bureaus
export const listBureaus = () => api.get('/api/bureaus')
export const getRoutingRules = () => api.get('/api/bureaus/routing-rules')
export const recommendBureau = (category) => api.get(`/api/bureaus/recommend/${encodeURIComponent(category)}`)

// Users
export const listOfficers = (bureauId) => api.get('/api/users/officers', { params: { bureau_id: bureauId } })
export const listUsers = (params) => api.get('/api/users', { params })

// Dashboard
export const getDashboardSummary = () => api.get('/api/dashboard/summary')
export const getWorkload = () => api.get('/api/dashboard/workload')
export const getTrends = (days = 30) => api.get('/api/dashboard/trends', { params: { days } })
export const getRecentActivity = () => api.get('/api/dashboard/recent-activity')

// Notifications
export const listNotifications = (unreadOnly = false) =>
  api.get('/api/notifications', { params: { unread_only: unreadOnly } })
export const unreadCount = () => api.get('/api/notifications/unread-count')
export const markRead = (id) => api.post(`/api/notifications/${id}/read`)
export const markAllRead = () => api.post('/api/notifications/read-all')

// Coordination
export const listCoordination = (params) => api.get('/api/coordination-requests', { params })
export const createCoordination = (data) => api.post('/api/coordination-requests', data)
export const respondCoordination = (id, data) => api.post(`/api/coordination-requests/${id}/respond`, data)

// Reports
export const exportCasesCsv = (params) =>
  api.get('/api/reports/cases.csv', { params, responseType: 'blob' })
export const exportCasesPdf = (params) =>
  api.get('/api/reports/cases.pdf', { params, responseType: 'blob' })
export const getAuditLogs = (limit = 100) => api.get('/api/reports/audit-logs', { params: { limit } })
