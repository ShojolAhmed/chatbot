import { ChatInput } from './ChatInput'

export function EmptyState({ onSend, isSending }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-4">
      <div className="w-full max-w-2xl">
        <div className="mb-8 text-center">
          <h1 className="text-[28px] font-medium tracking-tight text-text sm:text-[32px]">
            What's on your mind?
          </h1>
          <p className="mt-2.5 text-[15px] text-text-muted">
            Ask a question, brainstorm an idea, or start wherever feels right.
          </p>
        </div>

        <ChatInput onSend={onSend} isSending={isSending} autoFocus />
      </div>
    </div>
  )
}
