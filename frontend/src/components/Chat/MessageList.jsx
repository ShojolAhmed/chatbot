import { useEffect, useRef } from 'react'
import { Message } from './Message'
import { TypingIndicator } from './TypingIndicator'
import { ErrorBanner } from './ErrorBanner'

export function MessageList({ messages, isSending, error, onRetry }) {
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages.length, isSending, error])

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-6 sm:px-6">
      {messages.map((m) => (
        <Message key={m.id} role={m.role} text={m.text} />
      ))}

      {isSending && (
        <div className="flex justify-start">
          <TypingIndicator />
        </div>
      )}

      {error && <ErrorBanner message={error} onRetry={onRetry} />}

      <div ref={endRef} />
    </div>
  )
}
