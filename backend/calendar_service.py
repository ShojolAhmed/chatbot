"""Google Calendar API logic, separate from OAuth and from the LLM.

Exposes a single high-level function `create_event` that takes already
structured/validated data and creates either an all-day or a timed event on
the user's primary calendar.
"""

import logging
from datetime import datetime, date, time, timedelta

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from . import config, google_oauth

logger = logging.getLogger(__name__)


class CalendarNotConnectedError(Exception):
    """The user has not connected (or must reconnect) Google Calendar."""


class CalendarError(Exception):
    """A recoverable error talking to the Calendar API or bad event data."""


def _resolve_timezone() -> str:
    """Pick a timezone string for timed events.

    Prefers CALENDAR_TIMEZONE from config; otherwise falls back to the
    server's local UTC offset (e.g. "+06:00"), which Google accepts inside
    RFC3339 datetimes.
    """
    if config.CALENDAR_TIMEZONE:
        return config.CALENDAR_TIMEZONE
    return "UTC"


def _local_offset_suffix() -> str:
    """Return the local UTC offset as an RFC3339 suffix like '+06:00'.

    Used when no explicit IANA timezone is configured so timed events land at
    the intended wall-clock time.
    """
    offset = datetime.now().astimezone().utcoffset() or timedelta(0)
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    return f"{sign}{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def _parse_date(date_str: str) -> date:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError) as exc:
        raise CalendarError(f"Invalid date: {date_str!r}. Expected YYYY-MM-DD.") from exc


def _parse_time(time_str: str) -> time:
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(time_str, fmt).time()
        except (ValueError, TypeError):
            continue
    raise CalendarError(f"Invalid time: {time_str!r}. Expected HH:MM (24h).")


def _build_event_body(
    title: str,
    date_str: str,
    start_time: str | None,
    end_time: str | None,
    all_day: bool,
) -> dict:
    if not title or not title.strip():
        raise CalendarError("Event title is required.")

    event_date = _parse_date(date_str)

    if all_day or not start_time:
        # All-day event: Google uses date-only start, and an exclusive end
        # date of the following day for a single-day event.
        return {
            "summary": title.strip(),
            "start": {"date": event_date.isoformat()},
            "end": {"date": (event_date + timedelta(days=1)).isoformat()},
        }

    # Timed event.
    start_t = _parse_time(start_time)
    start_dt = datetime.combine(event_date, start_t)

    if end_time:
        end_t = _parse_time(end_time)
        end_dt = datetime.combine(event_date, end_t)
        # Handle an end that crosses midnight (e.g. 23:00 -> 00:30).
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)
    else:
        end_dt = start_dt + timedelta(minutes=config.DEFAULT_EVENT_DURATION_MINUTES)

    if config.CALENDAR_TIMEZONE:
        return {
            "summary": title.strip(),
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": config.CALENDAR_TIMEZONE,
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": config.CALENDAR_TIMEZONE,
            },
        }

    # No IANA tz configured: embed the local UTC offset in the RFC3339 value.
    offset = _local_offset_suffix()
    return {
        "summary": title.strip(),
        "start": {"dateTime": start_dt.isoformat() + offset},
        "end": {"dateTime": end_dt.isoformat() + offset},
    }


def create_event(
    user_id: str,
    title: str,
    date_str: str,
    start_time: str | None = None,
    end_time: str | None = None,
    all_day: bool = True,
) -> dict:
    """Create a calendar event for a user.

    Returns a small dict describing the created event on success.
    Raises CalendarNotConnectedError if the user must (re)connect Google,
    or CalendarError for bad data / API failures.
    """
    creds = google_oauth.load_credentials(user_id)
    if creds is None:
        raise CalendarNotConnectedError("Google Calendar is not connected.")

    body = _build_event_body(title, date_str, start_time, end_time, all_day)

    try:
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        created = (
            service.events()
            .insert(calendarId="primary", body=body)
            .execute()
        )
    except HttpError as exc:
        status = getattr(exc, "status_code", None) or getattr(exc.resp, "status", None)
        logger.error("Google Calendar API error (status=%s): %s", status, exc)
        if status in (401, 403):
            # Token likely revoked/insufficient -> ask user to reconnect.
            google_oauth.disconnect(user_id)
            raise CalendarNotConnectedError(
                "Google authorization is no longer valid."
            ) from exc
        raise CalendarError("Google Calendar rejected the request.") from exc
    except Exception as exc:  # network / transport / unexpected
        logger.exception("Unexpected error creating calendar event")
        raise CalendarError("Could not reach Google Calendar.") from exc

    return {
        "id": created.get("id"),
        "title": body["summary"],
        "html_link": created.get("htmlLink"),
        "all_day": "date" in body["start"],
        "start": body["start"].get("dateTime") or body["start"].get("date"),
        "end": body["end"].get("dateTime") or body["end"].get("date"),
    }
