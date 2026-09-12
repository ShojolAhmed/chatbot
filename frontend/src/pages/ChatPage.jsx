import { EmptyState } from '../components/Chat/EmptyState'
import { ChatContainer } from '../components/Chat/ChatContainer'
import { MobileTopBar } from '../components/Chat/MobileTopBar'

export function ChatPage({ chat }) {
  const { messages, isSending, error, hasStarted, sendMessage, retryLast } = chat

  return (
    <div className="flex h-full min-h-0 min-w-0 flex-1 flex-col">
      <MobileTopBar />

      <main className="min-h-0 flex-1 overflow-hidden">
        {hasStarted ? (
          <ChatContainer
            messages={messages}
            isSending={isSending}
            error={error}
            onSend={sendMessage}
            onRetry={retryLast}
          />
        ) : (
          <EmptyState onSend={sendMessage} isSending={isSending} />
        )}
      </main>
    </div>
  )
}
