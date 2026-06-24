/**
 * Chat state management hook.
 * Maintains conversation history and calls the RAG API.
 */

import { useCallback, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { sendChatMessage } from '../services/api'

export function useChat() {
  const [messages, setMessages] = useState([])   // {role, content, sources?, id}
  const [isLoading, setIsLoading] = useState(false)
  const abortRef = useRef(null)

  const sendMessage = useCallback(async (query, documentIds = null) => {
    if (!query.trim() || isLoading) return

    const userMsg = { id: Date.now(), role: 'user', content: query }
    setMessages((prev) => [...prev, userMsg])
    setIsLoading(true)

    // Build history in the format the backend expects
    const history = messages.map(({ role, content }) => ({ role, content }))

    try {
      const data = await sendChatMessage(query, history, documentIds)
      const assistantMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.answer,
        sources: data.sources ?? [],
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err) {
      toast.error(err.message || 'Failed to get a response')
      // Remove the user message on failure so they can retry
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id))
    } finally {
      setIsLoading(false)
    }
  }, [messages, isLoading])

  const clearConversation = useCallback(() => {
    setMessages([])
  }, [])

  return { messages, isLoading, sendMessage, clearConversation }
}
