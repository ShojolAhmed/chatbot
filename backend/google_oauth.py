"""Google OAuth 2.0 logic, kept separate from the Calendar API logic.

Responsibilities:
  * build the consent-screen URL
  * exchange the returned code for tokens
  * load stored credentials for a user and refresh them when expired

All secrets come from config (env vars). Tokens are persisted through
token_store, so this module has no opinion on the storage backend.
"""

import logging
from typing import Optional, Tuple

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import Flow

from . import config, token_store

logger = logging.getLogger(__name__)


class OAuthError(Exception):
    """Raised for recoverable OAuth problems (surface a friendly message)."""


def _build_flow(state: Optional[str] = None) -> Flow:
    return Flow.from_client_config(
        config.google_client_config(),
        scopes=config.GOOGLE_SCOPES,
        redirect_uri=config.GOOGLE_REDIRECT_URI,
        state=state,
    )


def build_authorization_url(state: str) -> tuple[str, Optional[str]]:
    """Return (consent URL, code_verifier) for the OAuth flow.

    `state` ties the callback back to the initiating session and is validated
    on return to mitigate CSRF. The library uses PKCE, so it generates a
    `code_verifier` that MUST be supplied again at token-exchange time; we
    return it here so the caller can persist it alongside the state.
    """
    flow = _build_flow(state=state)
    auth_url, _ = flow.authorization_url(
        access_type="offline",       # get a refresh token
        include_granted_scopes="true",
        prompt="consent",            # ensure refresh token on re-auth
    )
    return auth_url, getattr(flow, "code_verifier", None)


def _credentials_to_dict(creds: Credentials) -> dict:
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }


def exchange_code(code: str, state: Optional[str] = None,
                  code_verifier: Optional[str] = None) -> dict:
    """Exchange an authorization code for tokens and return a token dict.

    `code_verifier` is the PKCE verifier produced when the auth URL was built;
    it must match or Google rejects the exchange ("Missing code verifier").

    Raises OAuthError on failure.
    """
    try:
        flow = _build_flow(state=state)
        # Restore the PKCE verifier lost between the two separate requests.
        if code_verifier is not None:
            flow.code_verifier = code_verifier
        flow.fetch_token(code=code)
    except Exception as exc:  # library raises a variety of exception types
        # Log the concrete reason (scope change, invalid_grant, transport, ...)
        # so failures are diagnosable from the backend console.
        logger.exception("Failed to exchange OAuth code: %s: %s",
                         type(exc).__name__, exc)
        raise OAuthError(str(exc) or "Failed to complete Google authorization.") from exc

    return _credentials_to_dict(flow.credentials)


def load_credentials(user_id: str) -> Optional[Credentials]:
    """Load stored credentials for a user, refreshing if needed.

    Returns None when the user has not connected Google, or when stored
    credentials are unusable (in which case they are cleared so the user is
    prompted to reconnect). Refreshed tokens are persisted automatically.
    """
    token_data = token_store.get(user_id)
    if not token_data:
        return None

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
    )

    if creds.valid:
        return creds

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token_store.save(user_id, _credentials_to_dict(creds))
            return creds
        except RefreshError:
            # Refresh token revoked/expired -> force reconnect.
            logger.warning("Google refresh failed for user %s; clearing token", user_id)
            token_store.delete(user_id)
            return None
        except Exception:
            logger.exception("Unexpected error refreshing Google token")
            return None

    # No way to use these credentials.
    return None


def is_connected(user_id: str) -> bool:
    """True when the user has usable Google credentials."""
    return load_credentials(user_id) is not None


def disconnect(user_id: str) -> None:
    token_store.delete(user_id)
