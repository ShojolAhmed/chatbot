/**
 * Centralized runtime configuration.
 *
 * Keep every environment-derived value and every assumption about backend
 * endpoints/shapes here, instead of scattering them across the app. When the
 * real backend contract is finalized, this is the one file that should need
 * to change.
 */

// If VITE_API_BASE_URL is not set, requests are made same-origin (e.g. the
// frontend is served behind the same host/reverse proxy as the API), so
// `/api/chat` works without any extra configuration.
const rawBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()

export const API_BASE_URL = rawBaseUrl ? rawBaseUrl.replace(/\/$/, '') : ''

export const CHAT_ENDPOINT = `${API_BASE_URL}/api/chat`

// ---------------------------------------------------------------------------
// Auth configuration
// ---------------------------------------------------------------------------
// ASSUMPTION: the backend exposes (or will expose) endpoints roughly shaped
// like the ones below for Google OAuth. None of these are known to exist
// yet -- they are isolated here so the auth service (see authApi.js) can be
// pointed at the real endpoints later without touching any UI code.
export const AUTH_CONFIG = {
  // Kicks off the Google OAuth flow, e.g. by redirecting the browser here,
  // or by exchanging a Google credential for a session on this endpoint.
  googleSignInUrl: `${API_BASE_URL}/api/auth/google`,
  // Returns the current session's user, or 401 if signed out.
  sessionUrl: `${API_BASE_URL}/api/auth/session`,
  // Ends the current session.
  signOutUrl: `${API_BASE_URL}/api/auth/signout`,
  googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID ?? '',
}

export const IS_DEV = import.meta.env.DEV
