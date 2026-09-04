"""Central configuration for the chatbot and the Google Calendar integration.

All secrets/tunables come from environment variables (loaded from .env).
Nothing sensitive is hardcoded here.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- LLM / chat model -------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("BASE_URL")
CHAT_MODEL = os.getenv("CHAT_MODEL", "claude-opus-5")

# --- Google OAuth -----------------------------------------------------------

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "http://localhost:8000/api/auth/google/callback",
)

# Scope: create/manage events on the user's calendars.
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

# --- Local development OAuth flags ------------------------------------------
#
# oauthlib enforces two things that break a typical localhost dev setup:
#   1. It refuses OAuth over plain http:// (InsecureTransportError).
#   2. It raises "Scope has changed" when Google returns extra scopes
#      (e.g. it silently adds `openid`).
#
# When the redirect URI is a local http:// address we relax both, mirroring
# Google's own quickstart guidance. This is DEV-ONLY: over https in production
# these flags are left untouched so the strict behaviour applies.
if GOOGLE_REDIRECT_URI.startswith("http://") and (
    "localhost" in GOOGLE_REDIRECT_URI or "127.0.0.1" in GOOGLE_REDIRECT_URI
):
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
    os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

# --- Calendar behaviour -----------------------------------------------------

# Default duration (minutes) for a timed event when the user gives a start
# time but no end time. Change this single value to adjust the default.
DEFAULT_EVENT_DURATION_MINUTES = int(
    os.getenv("DEFAULT_EVENT_DURATION_MINUTES", "90")
)

# Optional IANA timezone (e.g. "Asia/Dhaka", "America/New_York").
# If unset, the server's local UTC offset is used for timed events.
CALENDAR_TIMEZONE = os.getenv("CALENDAR_TIMEZONE")

# --- Persistence ------------------------------------------------------------

# Simple local token store for development. Structured behind token_store.py
# so it can be swapped for a database later without touching callers.
BASE_DIR = Path(__file__).resolve().parent
TOKEN_STORE_PATH = Path(
    os.getenv("TOKEN_STORE_PATH", str(BASE_DIR / "google_tokens.json"))
)


def google_oauth_configured() -> bool:
    """True when the minimum Google OAuth env vars are present."""
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI)


def google_client_config() -> dict:
    """Build the client config dict expected by google-auth-oauthlib.

    Uses the "web" application flow. Raises if credentials are missing so the
    caller can surface a clear error instead of contacting Google with blanks.
    """
    if not google_oauth_configured():
        raise RuntimeError(
            "Google OAuth is not configured. Set GOOGLE_CLIENT_ID, "
            "GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI in your .env file."
        )

    return {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [GOOGLE_REDIRECT_URI],
        }
    }
