import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'

export function ChatContainer({ messages, isSending, error, onSend, onRetry }) {
  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto">
        <MessageList messages={messages} isSending={isSending} error={error} onRetry={onRetry} />
      </div>

      <div className="shrink-0 border-t border-border-soft bg-bg px-4 pb-5 pt-3 sm:px-6">
        <div className="mx-auto w-full max-w-3xl">
          <ChatInput onSend={onSend} isSending={isSending} />
        </div>
      </div>
    </div>
  )
}
