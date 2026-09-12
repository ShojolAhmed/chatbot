import { LogIn, LogOut } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

function initials(name) {
  if (!name) return '?'
  const parts = name.trim().split(/\s+/)
  return parts
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join('')
}

function Avatar({ user }) {
  const label = user?.name || user?.email || 'Account'
  if (user?.avatarUrl) {
    return (
      <img
        src={user.avatarUrl}
        alt=""
        className="h-8 w-8 shrink-0 rounded-full object-cover"
        referrerPolicy="no-referrer"
      />
    )
  }
  return (
    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-sidebar-hover text-xs font-medium text-text-muted">
      {initials(label)}
    </span>
  )
}

export function AccountSection({ collapsed, onExpand }) {
  const { isSignedIn, user, openSignIn, signOut } = useAuth()

  if (collapsed) {
    return (
      <div className="flex flex-col items-center border-t border-sidebar-border px-2 py-3">
        {isSignedIn ? (
          <button
            type="button"
            onClick={onExpand}
            aria-label="Account"
            title={user?.name || user?.email || 'Account'}
            className="rounded-full transition-opacity hover:opacity-80"
          >
            <Avatar user={user} />
          </button>
        ) : (
          <button
            type="button"
            onClick={openSignIn}
            aria-label="Sign in"
            title="Sign in"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-sidebar-hover hover:text-text"
          >
            <LogIn size={18} strokeWidth={1.75} aria-hidden="true" />
          </button>
        )}
      </div>
    )
  }

  if (!isSignedIn) {
    return (
      <div className="border-t border-sidebar-border px-3 py-3">
        <button
          type="button"
          onClick={openSignIn}
          className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium text-text transition-colors hover:bg-sidebar-hover"
        >
          <LogIn size={17} strokeWidth={1.75} className="text-text-muted" aria-hidden="true" />
          Sign in
        </button>
      </div>
    )
  }

  const displayName = user?.name || 'Signed in'
  const displaySecondary = user?.email

  return (
    <div className="border-t border-sidebar-border px-3 py-3">
      <div className="flex items-center gap-2.5 rounded-lg px-2 py-1.5">
        <Avatar user={user} />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-text">{displayName}</p>
          {displaySecondary && <p className="truncate text-xs text-text-faint">{displaySecondary}</p>}
        </div>
      </div>
      <button
        type="button"
        onClick={signOut}
        className="mt-1 flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-text-muted transition-colors hover:bg-sidebar-hover hover:text-text"
      >
        <LogOut size={16} strokeWidth={1.75} aria-hidden="true" />
        Sign out
      </button>
    </div>
  )
}
