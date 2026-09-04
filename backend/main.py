import logging
import secrets

from fastapi import FastAPI, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

from . import config, google_oauth, token_store
from .chatbot import chat
from .google_oauth import OAuthError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# The frontend is served separately (static file / dev server), so allow the
# browser to call the API cross-origin during development. The session id is
# passed explicitly by the client (header/query), so credentials are not
# required and a permissive origin is fine for local dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_USER = "default"

# In-memory map of OAuth `state` -> {session_id, code_verifier}. Validates the
# callback, ties the returned tokens to the browser session that started the
# flow, and preserves the PKCE verifier between the two requests.
_pending_states: dict[str, dict] = {}


def _session_id(explicit: str | None) -> str:
    """Resolve the session/user id from the client, or fall back to default."""
    return (explicit or "").strip() or DEFAULT_USER


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


@app.post("/api/chat")
def send_message(body: ChatRequest, x_session_id: str | None = Header(default=None)):
    session_id = _session_id(body.session_id or x_session_id)
    result = chat(body.message, user_id=session_id)
    return {
        "reply": result["reply"],
        "auth_required": result["auth_required"],
    }


@app.get("/api/calendar/status")
def calendar_status(session: str | None = None, x_session_id: str | None = Header(default=None)):
    session_id = _session_id(session or x_session_id)
    return {
        "connected": google_oauth.is_connected(session_id),
        "configured": config.google_oauth_configured(),
    }


@app.post("/api/calendar/disconnect")
def calendar_disconnect(session: str | None = None, x_session_id: str | None = Header(default=None)):
    session_id = _session_id(session or x_session_id)
    google_oauth.disconnect(session_id)
    return {"connected": False}


@app.get("/api/auth/google")
def auth_google(session: str | None = None):
    """Begin the OAuth flow: redirect the user to Google's consent screen."""
    session_id = _session_id(session)

    if not config.google_oauth_configured():
        return JSONResponse(
            status_code=500,
            content={"error": "Google OAuth is not configured on the server."},
        )

    state = secrets.token_urlsafe(24)

    try:
        auth_url, code_verifier = google_oauth.build_authorization_url(state)
    except Exception:
        logger.exception("Failed to build Google authorization URL")
        return JSONResponse(
            status_code=500,
            content={"error": "Could not start Google authorization."},
        )

    _pending_states[state] = {"session_id": session_id, "code_verifier": code_verifier}

    return RedirectResponse(auth_url)


def _callback_page(title: str, message: str) -> HTMLResponse:
    """Small self-closing page shown in the OAuth popup/tab."""
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:Arial,sans-serif;text-align:center;padding:40px;color:#333}}</style>
</head><body>
<h3>{title}</h3>
<p>{message}</p>
<script>
  if (window.opener) {{
    window.opener.postMessage({{ type: "google-calendar-auth" }}, "*");
    setTimeout(function () {{ window.close(); }}, 800);
  }}
</script>
</body></html>"""
    return HTMLResponse(content=html)


@app.get("/api/auth/google/callback")
def auth_google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    """OAuth redirect target: exchange the code and store credentials."""
    if error:
        logger.warning("Google OAuth returned error: %s", error)
        return _callback_page(
            "Authorization cancelled",
            "Google Calendar was not connected. You can close this window and try again.",
        )

    if not code or not state or state not in _pending_states:
        return _callback_page(
            "Authorization failed",
            "Invalid or expired authorization request. Please try connecting again.",
        )

    pending = _pending_states.pop(state)
    session_id = pending["session_id"]

    try:
        token_data = google_oauth.exchange_code(
            code, state=state, code_verifier=pending.get("code_verifier")
        )
    except OAuthError as exc:
        logger.error("OAuth token exchange failed: %s", exc)
        return _callback_page(
            "Authorization failed",
            "We couldn't complete Google authorization. Please try again.",
        )

    token_store.save(session_id, token_data)

    return _callback_page(
        "Google Calendar connected",
        "You're all set. You can close this window and return to the chat.",
    )
