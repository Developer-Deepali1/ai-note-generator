import axios from 'axios'

const base = (import.meta.env.VITE_API_URL as string) || ''

const api = axios.create({
	baseURL: base || '/',
	headers: { 'Content-Type': 'application/json' },
})

export const getHealth = () => api.get('/api/health')
export const getSessions = () => api.get('/api/sessions')
export const createSession = (payload: any) => api.post('/api/sessions', payload)
export const getSession = (id: string) => api.get(`/api/sessions/${id}`)
export const getSessionNotes = (id: string) => api.get(`/api/sessions/${id}/notes`)
export const createNote = (sessionId: string, payload: any) => api.post(`/api/sessions/${sessionId}/notes`, payload)

export const transcribe = (payload: any) => api.post('/api/audio/transcribe', payload)
export const trackEngagement = (payload: any) => api.post('/api/engagement/track', payload)
export const analyzeWebcamEmotion = (payload: { frame: string }) =>
	api.post('/api/emotion/webcam', payload)
export const pipelineAnalyze = (payload: any) => api.post('/api/pipeline/analyze', payload)

export default api
