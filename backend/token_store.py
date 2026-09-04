"""Very small persistence layer for OAuth tokens.

For development this stores tokens as JSON on disk, keyed by a session/user
id. It intentionally deals only in plain dicts (no Google types) so the
storage backend can later be replaced with a database by swapping this module
without touching OAuth or calendar code.
"""

import json
import threading
from typing import Optional

from . import config

_lock = threading.Lock()


def _read_all() -> dict:
    path = config.TOKEN_STORE_PATH
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        # Corrupt or unreadable store -> treat as empty rather than crash.
        return {}


def _write_all(data: dict) -> None:
    path = config.TOKEN_STORE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    tmp.replace(path)  # atomic on same filesystem


def get(user_id: str) -> Optional[dict]:
    """Return the stored token dict for a user, or None."""
    with _lock:
        return _read_all().get(user_id)


def save(user_id: str, token_data: dict) -> None:
    """Persist the token dict for a user."""
    with _lock:
        data = _read_all()
        data[user_id] = token_data
        _write_all(data)


def delete(user_id: str) -> None:
    """Remove any stored token for a user (used on revoke/expiry)."""
    with _lock:
        data = _read_all()
        if user_id in data:
            del data[user_id]
            _write_all(data)


def exists(user_id: str) -> bool:
    with _lock:
        return user_id in _read_all()
