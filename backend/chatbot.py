import os
import json
import logging
from datetime import datetime, timedelta

from openai import OpenAI, APIStatusError

from . import config, calendar_service
from .calendar_service import CalendarNotConnectedError, CalendarError

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.BASE_URL,
)

MAX_RETRIES = 3
MAX_TOOL_ITERATIONS = 5

# Per-session conversation history. Keyed by user/session id so multiple
# browsers don't share one another's context. (A single "default" user is
# used when the frontend does not supply a session id.)
conversations: dict[str, list] = {}


# --- Tool definitions -------------------------------------------------------

tools = [
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": (
                "Add an event or reminder to the user's Google Calendar. "
                "Only call this when the user clearly wants to schedule, add, "
                "or be reminded of something in the future. Do NOT call it for "
                "questions, general discussion, or statements about the past."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": (
                            "A concise, professional event title derived from the "
                            "user's message (e.g. 'Computer Network Mid Exam', "
                            "'Meeting with Rahim'). Do not add extra information."
                        ),
                    },
                    "date": {
                        "type": "string",
                        "description": (
                            "The event date resolved to an absolute date in "
                            "YYYY-MM-DD format, using the current date provided "
                            "in the system message to resolve relative phrases "
                            "like 'tomorrow' or 'next Sunday'."
                        ),
                    },
                    "start_time": {
                        "type": "string",
                        "description": (
                            "Start time in 24-hour HH:MM format if the user gave "
                            "a time. Omit or set null for an all-day event."
                        ),
                    },
                    "end_time": {
                        "type": "string",
                        "description": (
                            "End time in 24-hour HH:MM format if the user gave an "
                            "explicit end time. Omit or set null to use the "
                            "default duration."
                        ),
                    },
                    "all_day": {
                        "type": "boolean",
                        "description": (
                            "true when the user did NOT specify a time (all-day "
                            "event); false when a start time was given."
                        ),
                    },
                },
                "required": ["title", "date", "all_day"],
            },
        },
    }
]


# --- System prompt ----------------------------------------------------------

def _system_prompt() -> str:
    now = datetime.now().astimezone()
    tz_label = config.CALENDAR_TIMEZONE or f"UTC{now.strftime('%z')[:3]}:{now.strftime('%z')[3:]}"
    return (
        "You are a helpful assistant inside a chat app. You chat normally and "
        "you can also add events to the user's Google Calendar using the "
        "create_calendar_event tool.\n\n"
        f"The current date is {now.strftime('%A, %Y-%m-%d')} "
        f"(timezone: {tz_label}). "
        "Use this to resolve relative dates such as 'today', 'tomorrow', "
        "'this Friday', 'next Sunday', or 'next week' into an absolute "
        "YYYY-MM-DD date. 'next Sunday' means the Sunday of next week, not "
        "today even if today is Sunday.\n\n"
        "WHEN TO CREATE AN EVENT:\n"
        "- Call create_calendar_event only when the user is clearly telling you "
        "about something they want scheduled or remembered (an exam, meeting, "
        "appointment, deadline, etc.).\n"
        "- Do NOT create an event for questions (e.g. 'When is next Sunday?'), "
        "for general knowledge questions, or for statements about the past "
        "(e.g. 'My exam was last Sunday').\n\n"
        "TITLES:\n"
        "- Convert casual descriptions into concise, professional titles.\n"
        "- 'I have my Computer Network Mid next Sunday' -> 'Computer Network Mid Exam'.\n"
        "- 'DBMS final exam next Monday' -> 'DBMS Final Exam'.\n"
        "- 'meeting with Rahim tomorrow' -> 'Meeting with Rahim'.\n"
        "- 'doctor appointment Friday at 4' -> 'Doctor Appointment'.\n"
        "- Do not add unnecessary detail to titles.\n\n"
        "TIMES:\n"
        "- If the user gives no time, set all_day=true and leave start_time and "
        "end_time null.\n"
        "- If the user gives a start time only, set all_day=false, set "
        "start_time (24h HH:MM), and leave end_time null (a default duration is "
        "applied automatically).\n"
        "- If the user gives both a start and end time, set both. Convert "
        "am/pm to 24-hour time (e.g. '2' in an afternoon exam context is 14:00; "
        "'10 AM' is 10:00).\n\n"
        "CLARIFICATION:\n"
        "- If essential information is genuinely missing or ambiguous (e.g. the "
        "user says 'I have an exam next Sunday' without saying which subject), "
        "ask one short clarifying question instead of guessing. Do not ask about "
        "information that isn't required.\n\n"
        "RESPONSES:\n"
        "- After a successful event creation, confirm naturally using the "
        "provided human-readable time, e.g. 'Added \"Computer Network Mid Exam\" "
        "to your Google Calendar for Sunday, September 6.'\n"
        "- Never expose tool names, JSON, or internal details to the user."
    )


# --- Tool handling ----------------------------------------------------------

def _clean(value):
    """Normalise empty strings to None."""
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return value


def _friendly_when(result: dict) -> str:
    """Human-readable description of the created event's time."""
    try:
        if result.get("all_day"):
            d = datetime.strptime(result["start"], "%Y-%m-%d")
            return d.strftime("%A, %B ") + str(d.day)
        start = datetime.fromisoformat(result["start"])
        end = datetime.fromisoformat(result["end"])
        day = start.strftime("%A, %B ") + str(start.day)
        span = f"{start.strftime('%I:%M %p').lstrip('0')} - {end.strftime('%I:%M %p').lstrip('0')}"
        return f"{day}, {span}"
    except (ValueError, KeyError, TypeError):
        return result.get("start", "")


def handle_create_calendar_event(user_id: str, args: dict, context: dict) -> str:
    """Execute the tool call and return a JSON string tool result.

    `context` is mutated to flag when the frontend must prompt for Google
    authorization.
    """
    title = _clean(args.get("title"))
    date_str = _clean(args.get("date"))
    start_time = _clean(args.get("start_time"))
    end_time = _clean(args.get("end_time"))
    all_day = bool(args.get("all_day", start_time is None))

    if not title:
        return json.dumps({"status": "error", "error": "invalid_data",
                           "message": "Missing event title."})
    if not date_str:
        return json.dumps({"status": "error", "error": "invalid_data",
                           "message": "Missing event date."})

    try:
        result = calendar_service.create_event(
            user_id=user_id,
            title=title,
            date_str=date_str,
            start_time=start_time,
            end_time=end_time,
            all_day=all_day,
        )
    except CalendarNotConnectedError:
        context["auth_required"] = True
        return json.dumps({
            "status": "error",
            "error": "not_connected",
            "message": (
                "The user has not connected Google Calendar. Ask them to click "
                "the 'Connect Google Calendar' button, then try again."
            ),
        })
    except CalendarError as exc:
        return json.dumps({
            "status": "error",
            "error": "calendar_error",
            "message": f"Could not create the event: {exc}",
        })

    return json.dumps({
        "status": "success",
        "title": result["title"],
        "all_day": result["all_day"],
        "when": _friendly_when(result),
        "html_link": result.get("html_link"),
    })


def _dispatch_tool_call(user_id: str, tool_call, context: dict) -> str:
    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments or "{}")
    except json.JSONDecodeError:
        args = {}

    if name == "create_calendar_event":
        return handle_create_calendar_event(user_id, args, context)
    return json.dumps({"status": "error", "error": "unknown_tool",
                       "message": f"Unknown tool: {name}"})


# --- Public entry point -----------------------------------------------------

def chat(user_input: str, user_id: str = "default") -> dict:
    """Send a user message through the LLM (with calendar tool) and reply.

    Returns {"reply": str, "auth_required": bool}. `auth_required` is True when
    the user needs to connect Google Calendar before the action can proceed.
    """
    convo = conversations.setdefault(user_id, [])
    convo.append({"role": "user", "content": user_input})

    context = {"auth_required": False}

    for retry in range(MAX_RETRIES):
        try:
            for _ in range(MAX_TOOL_ITERATIONS):
                response = client.chat.completions.create(
                    model=config.CHAT_MODEL,
                    messages=[{"role": "system", "content": _system_prompt()}] + convo,
                    tools=tools,
                )

                message = response.choices[0].message

                if not message.tool_calls:
                    convo.append(message)
                    return {"reply": message.content, "auth_required": context["auth_required"]}

                convo.append(message)

                for tool_call in message.tool_calls:
                    result = _dispatch_tool_call(user_id, tool_call, context)
                    convo.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })

            # Too many tool iterations without a final answer.
            return {
                "reply": "Sorry, I got stuck processing that request. Please try again.",
                "auth_required": context["auth_required"],
            }

        except APIStatusError as e:
            logger.error("LLM API error %s: %s", e.status_code, e.message)
            if retry == MAX_RETRIES - 1:
                return {"reply": f"Error {e.status_code}: {e.message}", "auth_required": False}

    return {"reply": "Something went wrong.", "auth_required": False}
