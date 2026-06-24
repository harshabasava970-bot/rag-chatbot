/**
 * API service layer.
 * All requests go through axios with a base URL from env variables.
 * During local dev the Vite proxy forwards /api → localhost:8000.
 */

import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 120_000, // 2 min for LLM calls
  headers: { 'Content-Type': 'application/json' },
})

// Response interceptor for unified error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'
    return Promise.reject(new Error(message))
  },
)

// ---------------------------------------------------------------------------
// Document APIs
// ---------------------------------------------------------------------------

/** Upload a PDF file and process it. */
export const uploadDocument = async (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (evt) => {
      if (onProgress && evt.total) {
        onProgress(Math.round((evt.loaded * 100) / evt.total))
      }
    },
  })
  return data
}

/** Fetch the list of all uploaded documents. */
export const getDocuments = async () => {
  const { data } = await api.get('/documents')
  return data
}

/** Delete a document by ID. */
export const deleteDocument = async (docId) => {
  const { data } = await api.delete(`/documents/${docId}`)
  return data
}

// ---------------------------------------------------------------------------
// Chat API
// ---------------------------------------------------------------------------

/**
 * Send a chat message to the RAG pipeline.
 * @param {string} query
 * @param {Array<{role: string, content: string}>} conversationHistory
 * @param {string[]|null} documentIds  - restrict search to specific docs
 */
export const sendChatMessage = async (query, conversationHistory = [], documentIds = null) => {
  const { data } = await api.post('/chat', {
    query,
    conversation_history: conversationHistory,
    document_ids: documentIds,
    top_k: 5,
  })
  return data
}

// ---------------------------------------------------------------------------
// Health check
// ---------------------------------------------------------------------------

export const getHealth = async () => {
  const { data } = await api.get('/health')
  return data
}

export default api
