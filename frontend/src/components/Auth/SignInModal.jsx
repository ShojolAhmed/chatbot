import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { Logo } from '../UI/Logo'

function GoogleIcon(props) {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" {...props}>
      <path
        fill="#4285F4"
        d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.71v2.26h2.9c1.7-1.57 2.68-3.87 2.68-6.61Z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.47-.8 5.96-2.19l-2.9-2.26c-.81.54-1.85.86-3.06.86-2.35 0-4.34-1.59-5.05-3.72H.95v2.33A9 9 0 0 0 9 18Z"
      />
      <path
        fill="#FBBC05"
        d="M3.95 10.69A5.4 5.4 0 0 1 3.67 9c0-.59.1-1.16.28-1.69V4.98H.95A9 9 0 0 0 0 9c0 1.45.35 2.83.95 4.02l3-2.33Z"
      />
      <path
        fill="#EA4335"
        d="M9 3.58c1.32 0 2.51.46 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0A9 9 0 0 0 .95 4.98l3 2.33C4.66 5.17 6.65 3.58 9 3.58Z"
      />
    </svg>
  )
}

export function SignInModal() {
  const { isModalOpen, closeSignIn, signInWithGoogle, signInError } = useAuth()
  const dialogRef = useRef(null)
  const closeButtonRef = useRef(null)

  useEffect(() => {
    if (!isModalOpen) return
    closeButtonRef.current?.focus()

    function onKeyDown(e) {
      if (e.key === 'Escape') {
        closeSignIn()
        return
      }
      if (e.key === 'Tab') {
        const focusables = dialogRef.current?.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        )
        if (!focusables || focusables.length === 0) return
        const first = focusables[0]
        const last = focusables[focusables.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }

    document.addEventListener('keydown', onKeyDown)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = ''
    }
  }, [isModalOpen, closeSignIn])

  if (!isModalOpen) return null

  return (
    <div
      className="animate-fade-in fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) closeSignIn()
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="signin-heading"
        className="animate-scale-in relative w-full max-w-sm rounded-2xl border border-border bg-surface p-6 shadow-2xl shadow-black/40"
      >
        <button
          ref={closeButtonRef}
          type="button"
          onClick={closeSignIn}
          aria-label="Close sign in dialog"
          className="absolute right-4 top-4 rounded-md p-1 text-text-faint transition-colors hover:bg-surface-2 hover:text-text"
        >
          <X size={18} aria-hidden="true" />
        </button>

        <div className="flex flex-col items-center pt-2 text-center">
          <Logo />
          <h2 id="signin-heading" className="mt-5 text-lg font-semibold text-text">
            Sign in
          </h2>
          <p className="mt-1.5 text-sm leading-relaxed text-text-muted">
            Sign in to keep your conversations connected to your account.
          </p>

          <button
            type="button"
            onClick={signInWithGoogle}
            className="mt-6 flex w-full items-center justify-center gap-2.5 rounded-xl border border-border bg-text px-4 py-2.5 text-sm font-medium text-bg transition-colors hover:bg-[#dcd9d5]"
          >
            <GoogleIcon />
            Continue with Google
          </button>

          {signInError && (
            <p role="alert" className="mt-3 text-sm text-danger">
              {signInError}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
