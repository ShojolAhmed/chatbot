import { RotateCcw } from 'lucide-react'

export function ErrorBanner({ message, onRetry }) {
  return (
    <div
      role="alert"
      className="animate-rise flex items-center justify-between gap-3 rounded-xl border border-danger/25 bg-danger-muted px-4 py-3 text-sm text-text"
    >
      <span>{message}</span>
      <button
        type="button"
        onClick={onRetry}
        className="flex shrink-0 items-center gap-1.5 rounded-lg border border-border px-2.5 py-1 text-xs font-medium text-text transition-colors hover:bg-surface-2"
      >
        <RotateCcw size={13} aria-hidden="true" />
        Try again
      </button>
    </div>
  )
}
