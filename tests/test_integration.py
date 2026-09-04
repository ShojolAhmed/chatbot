"""Automated tests for the Google Calendar integration.

Run from the project root:

    .\\venv\\Scripts\\python.exe -m unittest tests.test_integration -v

These cover the deterministic backend logic:
  * all-day vs timed event bodies (+ default duration, explicit duration)
  * invalid data handling
  * not-connected / auth-required signalling
  * the LLM tool-call loop (with a mocked model and mocked Google API)
  * token storage round-trip

LLM-driven behaviour (intent detection, title wording, relative-date maths)
requires a live model + API key and is verified manually; here we feed the
tool the arguments the model would produce and assert the resulting behaviour.
"""

import json
import types
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from datetime import datetime

from googleapiclient.errors import HttpError

from backend import calendar_service, chatbot, token_store, config, google_oauth
from backend.calendar_service import CalendarNotConnectedError, CalendarError


# --- helpers to fake OpenAI message / tool_call objects ---------------------

def _tool_call(call_id, name, args):
    return types.SimpleNamespace(
        id=call_id,
        function=types.SimpleNamespace(name=name, arguments=json.dumps(args)),
    )


def _assistant_message(content=None, tool_calls=None):
    return types.SimpleNamespace(content=content, tool_calls=tool_calls)


def _completion(message):
    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


class EventBodyTests(unittest.TestCase):
    def setUp(self):
        # Deterministic timezone/duration for these tests.
        self._tz = mock.patch.object(config, "CALENDAR_TIMEZONE", None)
        self._dur = mock.patch.object(config, "DEFAULT_EVENT_DURATION_MINUTES", 90)
        self._tz.start()
        self._dur.start()

    def tearDown(self):
        self._tz.stop()
        self._dur.stop()

    def test_all_day_event(self):
        body = calendar_service._build_event_body(
            "Computer Network Mid Exam", "2026-09-06", None, None, True
        )
        self.assertEqual(body["start"], {"date": "2026-09-06"})
        # Google all-day end date is exclusive -> next day.
        self.assertEqual(body["end"], {"date": "2026-09-07"})
        self.assertEqual(body["summary"], "Computer Network Mid Exam")

    def test_all_day_when_no_start_time_even_if_all_day_false(self):
        body = calendar_service._build_event_body(
            "X", "2026-09-06", None, None, False
        )
        self.assertIn("date", body["start"])

    def test_timed_default_duration_90(self):
        body = calendar_service._build_event_body(
            "Computer Network Mid Exam", "2026-09-06", "10:00", None, False
        )
        start = datetime.fromisoformat(body["start"]["dateTime"])
        end = datetime.fromisoformat(body["end"]["dateTime"])
        self.assertEqual(start.strftime("%H:%M"), "10:00")
        self.assertEqual((end - start).total_seconds(), 90 * 60)

    def test_timed_default_duration_is_configurable_60(self):
        with mock.patch.object(config, "DEFAULT_EVENT_DURATION_MINUTES", 60):
            body = calendar_service._build_event_body(
                "X", "2026-09-06", "10:00", None, False
            )
            start = datetime.fromisoformat(body["start"]["dateTime"])
            end = datetime.fromisoformat(body["end"]["dateTime"])
            self.assertEqual(end.strftime("%H:%M"), "11:00")

    def test_timed_explicit_duration(self):
        body = calendar_service._build_event_body(
            "X", "2026-09-06", "10:00", "12:00", False
        )
        start = datetime.fromisoformat(body["start"]["dateTime"])
        end = datetime.fromisoformat(body["end"]["dateTime"])
        self.assertEqual(start.strftime("%H:%M"), "10:00")
        self.assertEqual(end.strftime("%H:%M"), "12:00")

    def test_timed_crosses_midnight(self):
        body = calendar_service._build_event_body(
            "X", "2026-09-06", "23:00", "00:30", False
        )
        start = datetime.fromisoformat(body["start"]["dateTime"])
        end = datetime.fromisoformat(body["end"]["dateTime"])
        self.assertGreater(end, start)
        self.assertEqual(end.strftime("%Y-%m-%d %H:%M"), "2026-09-07 00:30")

    def test_uses_iana_timezone_when_configured(self):
        with mock.patch.object(config, "CALENDAR_TIMEZONE", "Asia/Dhaka"):
            body = calendar_service._build_event_body(
                "X", "2026-09-06", "10:00", None, False
            )
            self.assertEqual(body["start"]["timeZone"], "Asia/Dhaka")
            self.assertEqual(body["start"]["dateTime"], "2026-09-06T10:00:00")

    def test_invalid_date_raises(self):
        with self.assertRaises(CalendarError):
            calendar_service._build_event_body("X", "06-09-2026", None, None, True)

    def test_invalid_time_raises(self):
        with self.assertRaises(CalendarError):
            calendar_service._build_event_body("X", "2026-09-06", "25:99", None, False)

    def test_empty_title_raises(self):
        with self.assertRaises(CalendarError):
            calendar_service._build_event_body("   ", "2026-09-06", None, None, True)


class LocalOffsetTests(unittest.TestCase):
    def test_offset_format(self):
        import re
        self.assertRegex(calendar_service._local_offset_suffix(), r"^[+-]\d\d:\d\d$")


class CreateEventTests(unittest.TestCase):
    def test_not_connected_raises(self):
        with mock.patch.object(google_oauth, "load_credentials", return_value=None):
            with self.assertRaises(CalendarNotConnectedError):
                calendar_service.create_event("u", "X", "2026-09-06")

    def test_success_all_day(self):
        fake_service = mock.MagicMock()
        fake_service.events.return_value.insert.return_value.execute.return_value = {
            "id": "evt1",
            "htmlLink": "https://calendar.google.com/evt1",
        }
        with mock.patch.object(google_oauth, "load_credentials", return_value=object()), \
             mock.patch.object(calendar_service, "build", return_value=fake_service) as build_mock:
            result = calendar_service.create_event(
                "u", "Computer Network Mid Exam", "2026-09-06", all_day=True
            )

        build_mock.assert_called_once()
        _, kwargs = fake_service.events.return_value.insert.call_args
        self.assertEqual(kwargs["calendarId"], "primary")
        self.assertEqual(kwargs["body"]["start"], {"date": "2026-09-06"})
        self.assertTrue(result["all_day"])
        self.assertEqual(result["title"], "Computer Network Mid Exam")
        self.assertEqual(result["html_link"], "https://calendar.google.com/evt1")

    def test_http_401_forces_reconnect(self):
        resp = types.SimpleNamespace(status=401, reason="Unauthorized")
        err = HttpError(resp, b"{}")
        fake_service = mock.MagicMock()
        fake_service.events.return_value.insert.return_value.execute.side_effect = err
        with mock.patch.object(google_oauth, "load_credentials", return_value=object()), \
             mock.patch.object(calendar_service, "build", return_value=fake_service), \
             mock.patch.object(google_oauth, "disconnect") as disconnect_mock:
            with self.assertRaises(CalendarNotConnectedError):
                calendar_service.create_event("u", "X", "2026-09-06")
            disconnect_mock.assert_called_once_with("u")

    def test_http_500_raises_calendar_error(self):
        resp = types.SimpleNamespace(status=500, reason="Server Error")
        err = HttpError(resp, b"{}")
        fake_service = mock.MagicMock()
        fake_service.events.return_value.insert.return_value.execute.side_effect = err
        with mock.patch.object(google_oauth, "load_credentials", return_value=object()), \
             mock.patch.object(calendar_service, "build", return_value=fake_service):
            with self.assertRaises(CalendarError):
                calendar_service.create_event("u", "X", "2026-09-06")


class ToolHandlerTests(unittest.TestCase):
    def test_success_sets_no_auth_flag(self):
        context = {"auth_required": False}
        fake = {
            "id": "e", "title": "Computer Network Mid Exam", "html_link": "http://x",
            "all_day": True, "start": "2026-09-06", "end": "2026-09-07",
        }
        with mock.patch.object(calendar_service, "create_event", return_value=fake):
            out = json.loads(chatbot.handle_create_calendar_event(
                "u", {"title": "Computer Network Mid Exam", "date": "2026-09-06", "all_day": True}, context
            ))
        self.assertEqual(out["status"], "success")
        self.assertIn("September 6", out["when"])
        self.assertFalse(context["auth_required"])

    def test_not_connected_sets_auth_flag(self):
        context = {"auth_required": False}
        with mock.patch.object(calendar_service, "create_event",
                               side_effect=CalendarNotConnectedError()):
            out = json.loads(chatbot.handle_create_calendar_event(
                "u", {"title": "X", "date": "2026-09-06", "all_day": True}, context
            ))
        self.assertEqual(out["error"], "not_connected")
        self.assertTrue(context["auth_required"])

    def test_missing_title_is_invalid(self):
        context = {"auth_required": False}
        with mock.patch.object(calendar_service, "create_event") as ce:
            out = json.loads(chatbot.handle_create_calendar_event(
                "u", {"date": "2026-09-06", "all_day": True}, context
            ))
            ce.assert_not_called()
        self.assertEqual(out["error"], "invalid_data")

    def test_calendar_error_reported(self):
        context = {"auth_required": False}
        with mock.patch.object(calendar_service, "create_event",
                               side_effect=CalendarError("bad")):
            out = json.loads(chatbot.handle_create_calendar_event(
                "u", {"title": "X", "date": "2026-09-06", "all_day": True}, context
            ))
        self.assertEqual(out["error"], "calendar_error")


class FriendlyWhenTests(unittest.TestCase):
    def test_all_day(self):
        s = chatbot._friendly_when({"all_day": True, "start": "2026-09-06"})
        self.assertEqual(s, "Sunday, September 6")

    def test_timed(self):
        s = chatbot._friendly_when({
            "all_day": False,
            "start": "2026-09-06T10:00:00+06:00",
            "end": "2026-09-06T11:30:00+06:00",
        })
        self.assertIn("Sunday, September 6", s)
        self.assertIn("10:00 AM", s)
        self.assertIn("11:30 AM", s)


class ChatLoopTests(unittest.TestCase):
    """End-to-end chat() with a mocked model + mocked calendar."""

    def setUp(self):
        chatbot.conversations.clear()

    def test_tool_call_success_flow(self):
        responses = [
            _completion(_assistant_message(tool_calls=[
                _tool_call("c1", "create_calendar_event",
                           {"title": "Computer Network Mid Exam",
                            "date": "2026-09-06", "all_day": True})
            ])),
            _completion(_assistant_message(
                content='Added "Computer Network Mid Exam" to your Google Calendar for Sunday, September 6.'
            )),
        ]
        fake = {"id": "e", "title": "Computer Network Mid Exam", "html_link": "http://x",
                "all_day": True, "start": "2026-09-06", "end": "2026-09-07"}
        with mock.patch.object(chatbot.client.chat.completions, "create",
                               side_effect=responses) as create_mock, \
             mock.patch.object(calendar_service, "create_event", return_value=fake) as ce:
            result = chatbot.chat("I have my Computer Network Mid next Sunday", user_id="tester")

        self.assertFalse(result["auth_required"])
        self.assertIn("Computer Network Mid Exam", result["reply"])
        self.assertEqual(create_mock.call_count, 2)
        _, kwargs = ce.call_args
        self.assertEqual(kwargs["date_str"], "2026-09-06")
        self.assertTrue(kwargs["all_day"])

    def test_tool_call_not_connected_flow(self):
        responses = [
            _completion(_assistant_message(tool_calls=[
                _tool_call("c1", "create_calendar_event",
                           {"title": "X", "date": "2026-09-06", "all_day": True})
            ])),
            _completion(_assistant_message(
                content="You'll need to connect Google Calendar first."
            )),
        ]
        with mock.patch.object(chatbot.client.chat.completions, "create",
                               side_effect=responses), \
             mock.patch.object(calendar_service, "create_event",
                               side_effect=CalendarNotConnectedError()):
            result = chatbot.chat("I have my Computer Network Mid next Sunday", user_id="tester2")

        self.assertTrue(result["auth_required"])

    def test_plain_message_no_tool(self):
        responses = [
            _completion(_assistant_message(content="Computer networks cover routing, TCP/IP, and more.")),
        ]
        with mock.patch.object(chatbot.client.chat.completions, "create",
                               side_effect=responses), \
             mock.patch.object(calendar_service, "create_event") as ce:
            result = chatbot.chat("What topics are in Computer Networks?", user_id="tester3")
            ce.assert_not_called()
        self.assertFalse(result["auth_required"])
        self.assertIn("routing", result["reply"])


class TokenStoreTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "tokens.json"
            with mock.patch.object(config, "TOKEN_STORE_PATH", path):
                self.assertFalse(token_store.exists("u"))
                self.assertIsNone(token_store.get("u"))
                token_store.save("u", {"token": "abc"})
                self.assertTrue(token_store.exists("u"))
                self.assertEqual(token_store.get("u"), {"token": "abc"})
                token_store.delete("u")
                self.assertFalse(token_store.exists("u"))


class OAuthConfigTests(unittest.TestCase):
    def test_not_connected_when_no_token(self):
        with mock.patch.object(token_store, "get", return_value=None):
            self.assertFalse(google_oauth.is_connected("nobody"))

    def test_client_config_requires_env(self):
        with mock.patch.object(config, "GOOGLE_CLIENT_ID", None):
            self.assertFalse(config.google_oauth_configured())
            with self.assertRaises(RuntimeError):
                config.google_client_config()


class PkceTests(unittest.TestCase):
    """Lock in the PKCE fix: the verifier must survive between requests."""

    _FAKE_CFG = {
        "web": {
            "client_id": "x",
            "client_secret": "y",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8000/api/auth/google/callback"],
        }
    }

    def test_auth_url_includes_pkce_and_returns_verifier(self):
        with mock.patch.object(config, "google_client_config", return_value=self._FAKE_CFG), \
             mock.patch.object(config, "GOOGLE_REDIRECT_URI",
                               "http://localhost:8000/api/auth/google/callback"):
            url, verifier = google_oauth.build_authorization_url("state123")
        self.assertIn("code_challenge=", url)
        self.assertTrue(verifier)

    def test_exchange_applies_code_verifier(self):
        captured = {}

        class FakeFlow:
            def __init__(self):
                self.code_verifier = None
                self.credentials = types.SimpleNamespace(
                    token="t", refresh_token="r", token_uri="u",
                    client_id="c", client_secret="s", scopes=["scope"],
                )

            def fetch_token(self, code=None):
                captured["verifier_at_fetch"] = self.code_verifier
                captured["code"] = code

        with mock.patch.object(google_oauth, "_build_flow", return_value=FakeFlow()):
            out = google_oauth.exchange_code("thecode", state="s", code_verifier="VERIF")

        self.assertEqual(captured["verifier_at_fetch"], "VERIF")
        self.assertEqual(captured["code"], "thecode")
        self.assertEqual(out["token"], "t")
        self.assertEqual(out["refresh_token"], "r")


if __name__ == "__main__":
    unittest.main()
