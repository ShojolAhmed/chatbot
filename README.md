# Simple Chatbot

A simple AI conversation app built with Python and a basic frontend. It sends
messages to an AI model, shows the responses in a chat interface, and can add
events to your **Google Calendar** through natural language.

## Features

* Simple chat interface
* AI-powered conversations
* Python backend with FastAPI
* REST API for sending messages
* **Google Calendar integration** via LLM tool calling
  * Understands natural language ("I have my Computer Network Mid next Sunday")
  * Creates all-day or timed events
  * Resolves relative dates (today, tomorrow, next Sunday, this Friday, ...)
  * Google OAuth 2.0 with a minimal "Connect Google Calendar" flow

## Tech Stack

* Python + FastAPI
* OpenAI-compatible API (tool calling)
* Google Calendar API + OAuth 2.0
* HTML, CSS, JavaScript

## Project Structure

```
backend/
  main.py              FastAPI app + routes (chat, OAuth, calendar status)
  chatbot.py           LLM loop + create_calendar_event tool wiring
  config.py            Env-based configuration and defaults
  google_oauth.py      OAuth 2.0 logic (auth URL, code exchange, refresh)
  calendar_service.py  Google Calendar API logic (all-day / timed events)
  token_store.py       Simple JSON token persistence (swap for a DB later)
frontend/
  index.html           Chat UI + Connect Google Calendar banner
  app.js               Chat + OAuth popup flow + retry
  style.css            Styling
```

The Google Calendar logic (`calendar_service.py`), OAuth logic
(`google_oauth.py`), token storage (`token_store.py`), and LLM logic
(`chatbot.py`) are intentionally kept separate.

---

## How the Google Calendar integration works

```
User -> Frontend -> FastAPI -> LLM
                                 |
                 LLM decides to call create_calendar_event
                                 |
                        calendar_service -> Google Calendar API
                                 |
                        tool result -> LLM -> chat reply
```

* The LLM receives the current date in its system prompt and resolves relative
  dates itself, then calls `create_calendar_event` with an absolute
  `YYYY-MM-DD` date.
* If the user gives **no time**, an **all-day** event is created.
* If the user gives a **start time only**, a timed event is created with a
  default duration (90 minutes, configurable via `DEFAULT_EVENT_DURATION_MINUTES`).
* If the user gives **both times**, the exact span is used.
* If the user is not connected to Google, the backend returns
  `auth_required: true`; the frontend shows a **Connect Google Calendar**
  button and retries the original message after a successful connection.

---

## Google Cloud setup

1. **Create / select a project**
   Go to the [Google Cloud Console](https://console.cloud.google.com/).

2. **Enable the Google Calendar API**
   APIs & Services -> Library -> search "Google Calendar API" -> **Enable**.

3. **Configure the OAuth consent screen**
   APIs & Services -> OAuth consent screen.
   * User type: **External** (fine for testing).
   * Fill in the required app name / support email.
   * Add the scope `.../auth/calendar.events`.
   * Add your Google account under **Test users** (required while the app is in
     "Testing").

4. **Create OAuth credentials**
   APIs & Services -> Credentials -> **Create Credentials** -> **OAuth client ID**.
   * Application type: **Web application**.
   * **Authorized redirect URI** (must match exactly):
     ```
     http://localhost:8000/api/auth/google/callback
     ```
   * Copy the **Client ID** and **Client secret**.

---

## Environment variables

Copy `.env.example` to `.env` and fill in the values:

```env
OPENAI_API_KEY=your-api-key
BASE_URL=api-base-url
CHAT_MODEL=claude-opus-5

GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

DEFAULT_EVENT_DURATION_MINUTES=90
CALENDAR_TIMEZONE=Asia/Dhaka
```

* `GOOGLE_REDIRECT_URI` must match the redirect URI configured in Google Cloud.
* `CALENDAR_TIMEZONE` is optional. If unset, the server's local UTC offset is
  used for timed events. Set it to an IANA name (e.g. `Asia/Dhaka`) for
  predictable results.
* **Never commit `.env`** or `backend/google_tokens.json` (both are gitignored).

---

## Running the app

1. **Create a virtual environment and install dependencies**

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Start the backend** (from the project root)

   ```powershell
   uvicorn backend.main:app --reload --port 8000
   ```

3. **Open the frontend**
   Open `frontend/index.html` in your browser (or serve it with any static
   server, e.g. VS Code Live Server). The frontend talks to the API at
   `http://127.0.0.1:8000`.

4. **Connect Google Calendar**
   Send a scheduling message (e.g. "I have my Computer Network Mid next
   Sunday"). If you aren't connected yet, click **Connect Google Calendar**,
   complete the Google consent screen, and the message is retried
   automatically.

---

## Troubleshooting OAuth

**"Access blocked: ChatBot has not completed the Google verification process"**
Your OAuth consent screen is in **Testing** mode, so only approved accounts can
connect. Google Cloud Console -> APIs & Services -> OAuth consent screen ->
**Test users** -> **Add users** -> add the exact Gmail address you sign in with
(you must also *select* that same account on the consent screen). Up to 100 test
users are allowed. Publishing to Production removes this block but requires
Google verification for the sensitive `calendar.events` scope.

**"Authorization failed / we couldn't complete Google authorization"**
This is the backend token-exchange step failing (check the server console for
the exact reason). For local `http://localhost` development the two usual causes
are handled automatically in `config.py`:
* `OAUTHLIB_INSECURE_TRANSPORT=1` - oauthlib otherwise refuses OAuth over plain
  `http://`.
* `OAUTHLIB_RELAX_TOKEN_SCOPE=1` - Google may return extra scopes (e.g. `openid`),
  which oauthlib otherwise rejects as "Scope has changed".

These flags are applied only when `GOOGLE_REDIRECT_URI` is a local `http://`
address; over `https` in production the strict behaviour is kept. If it still
fails, confirm the redirect URI in `.env` **exactly** matches the one registered
in Google Cloud (scheme, host, port, and path), and that the authorization code
hasn't expired (each code is single-use; just click Connect again).

---

## Notes

* Token storage is a simple local JSON file (`backend/google_tokens.json`) for
  development. It is isolated behind `token_store.py` so it can be replaced
  with a database without changing OAuth or calendar code.
* Sessions are identified by a random id generated in the browser
  (`localStorage`) and sent with each request. This ties chat history and
  Google credentials to a browser without a full auth system.
