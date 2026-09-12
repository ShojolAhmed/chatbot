import { AUTH_CONFIG } from './config'

/**
 * Auth service -- isolates all assumptions about the (not-yet-provided)
 * Google OAuth backend so the rest of the app only ever talks to the
 * functions below.
 *
 * How this is meant to plug in for real:
 *  - `signInWithGoogle` should redirect to (or open) the backend's OAuth
 *    entry point, which in turn redirects to Google and back with a
 *    session cookie set. Until that endpoint exists, this throws so the UI
 *    can show a clear "not connected yet" state instead of pretending to
 *    succeed.
 *  - `getSession` checks whether a session already exists (e.g. on app
 *    load) by calling the backend, which reads its own session cookie.
 *  - `signOut` clears that session.
 *
 * No credentials, tokens, or client secrets are ever stored here -- session
 * state is expected to live in an httpOnly cookie managed by the backend.
 */

async function getSession({ signal } = {}) {
  try {
    const res = await fetch(AUTH_CONFIG.sessionUrl, {
      credentials: 'include',
      signal,
    })
    if (!res.ok) return null
    const data = await res.json()
    return data?.user ?? null
  } catch {
    // No backend wired up yet, or the user simply isn't signed in.
    return null
  }
}

function signInWithGoogle() {
  // Full-page redirect into the backend's OAuth flow. Swap this for a
  // popup-based flow if the backend prefers postMessage-based handoff.
  window.location.href = AUTH_CONFIG.googleSignInUrl
}

async function signOut() {
  try {
    await fetch(AUTH_CONFIG.signOutUrl, {
      method: 'POST',
      credentials: 'include',
    })
  } catch {
    // Even if the request fails, the UI proceeds to clear local auth state.
  }
}

export const authApi = { getSession, signInWithGoogle, signOut }
