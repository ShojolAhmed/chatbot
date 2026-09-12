import { SquarePen } from 'lucide-react'

export function NewChatButton({ collapsed, onClick, disabled }) {
  if (collapsed) {
    return (
      <div className="flex justify-center px-2">
        <button
          type="button"
          onClick={onClick}
          disabled={disabled}
          aria-label="New chat"
          title="New chat"
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-sidebar-border text-text transition-colors hover:bg-sidebar-hover disabled:opacity-50"
        >
          <SquarePen size={17} strokeWidth={1.75} aria-hidden="true" />
        </button>
      </div>
    )
  }

  return (
    <div className="px-3">
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        className="flex w-full items-center gap-2 rounded-lg border border-sidebar-border px-3 py-2 text-sm font-medium text-text transition-colors hover:bg-sidebar-hover disabled:opacity-50"
      >
        <SquarePen size={16} strokeWidth={1.75} aria-hidden="true" />
        New chat
      </button>
    </div>
  )
}
