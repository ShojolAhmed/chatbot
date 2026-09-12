export function ConversationItem({ title, isActive = false, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={isActive ? 'true' : undefined}
      className={`block w-full truncate rounded-lg px-2.5 py-2 text-left text-sm transition-colors ${
        isActive ? 'bg-sidebar-active text-text' : 'text-text-muted hover:bg-sidebar-hover hover:text-text'
      }`}
    >
      {title}
    </button>
  )
}
