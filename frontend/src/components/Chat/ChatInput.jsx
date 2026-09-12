import { useRef, useState } from 'react'
import { ArrowUp } from 'lucide-react'
import { useAutoResizeTextarea } from '../../hooks/useAutoResizeTextarea'

export function ChatInput({ onSend, isSending, autoFocus = false, placeholder = 'Message...' }) {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)
  useAutoResizeTextarea(textareaRef, value)

  const canSend = value.trim().length > 0 && !isSending

  function handleSubmit(e) {
    e.preventDefault()
    if (!canSend) return
    onSend(value)
    setValue('')
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex items-end gap-2 rounded-2xl border border-border bg-surface px-3 py-2.5 shadow-sm shadow-black/10 transition-colors focus-within:border-text-faint">
        <label htmlFor="chat-input" className="sr-only">
          Message
        </label>
        <textarea
          ref={textareaRef}
          id="chat-input"
          rows={1}
          autoFocus={autoFocus}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="max-h-[200px] flex-1 resize-none bg-transparent py-1 text-base leading-6 text-text placeholder:text-text-faint focus:outline-none"
        />
        <button
          type="submit"
          disabled={!canSend}
          aria-label="Send message"
          className="mb-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent text-[#1a140f] transition-all enabled:hover:bg-accent-hover disabled:cursor-not-allowed disabled:bg-surface-2 disabled:text-text-faint"
        >
          <ArrowUp size={17} strokeWidth={2.5} aria-hidden="true" />
        </button>
      </div>
      <p className="mt-2 text-center text-xs text-text-faint">
        Press Enter to send, Shift + Enter for a new line
      </p>
    </form>
  )
}
