import { useCallback, useRef, useState } from 'react'
import { chatApi, normalizeChatResponse } from '../services/chatApi'

let idCounter = 0
const nextId = () => `msg_${Date.now()}_${idCounter++}`

/**
 * Owns the in-memory conversation for the current session. Nothing here is
 * persisted -- refreshing the page starts a new conversation, by design.
 */
export function useChat() {
  const [messages, setMessages] = useState([])
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState(null)
  const pendingRef = useRef(false)
  const lastFailedTextRef = useRef(null)

  const requestAssistantReply = useCallback(async (text) => {
    pendingRef.current = true
    setIsSending(true)
    setError(null)
    try {
      const payload = await chatApi.sendMessage(text)
      const { text: assistantText } = normalizeChatResponse(payload)
      setMessages((prev) => [...prev, { id: nextId(), role: 'assistant', text: assistantText }])
      lastFailedTextRef.current = null
    } catch (err) {
      lastFailedTextRef.current = text
      setError(err?.message || 'Something went wrong. Please try again.')
    } finally {
      setIsSending(false)
      pendingRef.current = false
    }
  }, [])

  const sendMessage = useCallback(
    async (rawText) => {
      const text = rawText.trim()
      if (!text || pendingRef.current) return
      setMessages((prev) => [...prev, { id: nextId(), role: 'user', text }])
      await requestAssistantReply(text)
    },
    [requestAssistantReply],
  )

  const retryLast = useCallback(() => {
    if (pendingRef.current || !lastFailedTextRef.current) return
    requestAssistantReply(lastFailedTextRef.current)
  }, [requestAssistantReply])

  const dismissError = useCallback(() => setError(null), [])

  const startNewChat = useCallback(() => {
    if (pendingRef.current) return
    setMessages([])
    setError(null)
    lastFailedTextRef.current = null
  }, [])

  return {
    messages,
    isSending,
    error,
    hasStarted: messages.length > 0,
    sendMessage,
    retryLast,
    dismissError,
    startNewChat,
  }
}
