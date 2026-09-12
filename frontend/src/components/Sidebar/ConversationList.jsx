import { MessageSquare } from 'lucide-react'
import { ConversationItem } from './ConversationItem'

// `conversations` is intentionally always empty for now -- there is no
// backend endpoint yet to list past conversations. Once one exists, pass
// the fetched list in here; the rendering below already handles it.
export function ConversationList({ collapsed, conversations = [] }) {
  if (collapsed) {
    return (
      <div className="flex flex-col items-center px-2 pt-1">
        <div
          className="flex h-9 w-9 items-center justify-center rounded-lg text-text-faint"
          title="Conversations"
          aria-label="Conversations"
        >
          <MessageSquare size={17} strokeWidth={1.75} aria-hidden="true" />
        </div>
      </div>
    )
  }

  return (
    <div className="px-3 pt-5">
      <h2 className="px-0.5 pb-1.5 text-xs font-medium uppercase tracking-wide text-text-faint">
        Conversations
      </h2>

      {conversations.length === 0 ? (
        <p className="px-0.5 py-1 text-sm text-text-faint">No conversations yet</p>
      ) : (
        <div className="flex flex-col gap-0.5">
          {conversations.map((conversation) => (
            <ConversationItem
              key={conversation.id}
              title={conversation.title}
              isActive={conversation.isActive}
              onClick={conversation.onClick}
            />
          ))}
        </div>
      )}
    </div>
  )
}
