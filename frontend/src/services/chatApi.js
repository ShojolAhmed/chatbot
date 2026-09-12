import { CHAT_ENDPOINT } from './config'

/**
 * ApiError carries the HTTP status alongside a user-safe message so callers
 * can distinguish network failures from backend-reported errors without
 * parsing strings.
 */
export class ApiError extends Error {
  constructor(message, { status, cause } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.cause = cause
  }
}

/**
 * Sends the user's message to POST /api/chat.
 *
 * Request body is exactly `{ message: string }` per the backend contract.
 * Returns the raw parsed JSON response -- callers should pass it through
 * `normalizeChatResponse` rather than reading fields directly, since the
 * exact response shape isn't finalized yet.
 */
async function sendMessage(message, { signal } = {}) {
  let response
  try {
    response = await fetch(CHAT_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
      signal,
    })
  } catch (err) {
    if (err.name === 'AbortError') throw err
    throw new ApiError('Could not reach the server. Check your connection and try again.', {
      cause: err,
    })
  }

  let payload = null
  const text = await response.text()
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      // Non-JSON response body; leave payload null and fall back to status text below.
    }
  }

  if (!response.ok) {
    const backendMessage = payload?.error || payload?.message
    throw new ApiError(backendMessage || 'Something went wrong. Please try again.', {
      status: response.status,
    })
  }

  return payload
}

/**
 * Normalizes whatever shape the backend currently returns into the single
 * shape the UI relies on: `{ text: string }`.
 *
 * ASSUMPTION (isolated here on purpose): the exact response JSON structure
 * isn't known yet. This function tries a handful of plausible shapes --
 * `{ reply }`, `{ message }`, `{ response }`, `{ content }`, or a plain
 * string -- so that only this function needs to change once the real
 * contract is confirmed, rather than every place a response is displayed.
 */
export function normalizeChatResponse(payload) {
  if (typeof payload === 'string') {
    return { text: payload }
  }

  const text =
    payload?.reply ??
    payload?.message ??
    payload?.response ??
    payload?.content ??
    payload?.text ??
    null

  if (typeof text !== 'string' || !text.trim()) {
    throw new ApiError("Received an unexpected response from the server.")
  }

  return { text }
}

export const chatApi = { sendMessage }
