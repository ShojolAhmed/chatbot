const API_BASE = "http://127.0.0.1:8000";

const input = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const messages = document.getElementById("messages");
const connectBanner = document.getElementById("connectBanner");
const connectButton = document.getElementById("connectButton");
const calendarStatus = document.getElementById("calendarStatus");

// A stable per-browser session id. Ties chat history and Google credentials
// together on the backend without needing a full auth system.
let sessionId = localStorage.getItem("chat_session_id");
if (!sessionId) {
    sessionId = (crypto.randomUUID && crypto.randomUUID()) ||
        String(Date.now()) + Math.random().toString(16).slice(2);
    localStorage.setItem("chat_session_id", sessionId);
}

// Remembers the last user message so we can retry it after connecting Google.
let pendingCalendarMessage = null;


function addMessage(text, sender) {
    const message = document.createElement("div");

    message.classList.add("message");
    message.classList.add(sender);

    message.textContent = text;

    messages.appendChild(message);

    messages.scrollTop = messages.scrollHeight;
}


function setConnected(connected) {
    if (connected) {
        calendarStatus.textContent = "Google Calendar connected";
        calendarStatus.classList.add("connected");
        connectBanner.hidden = true;
    } else {
        calendarStatus.textContent = "";
        calendarStatus.classList.remove("connected");
    }
}


async function refreshCalendarStatus() {
    try {
        const response = await fetch(
            `${API_BASE}/api/calendar/status?session=${encodeURIComponent(sessionId)}`
        );
        const data = await response.json();
        setConnected(data.connected);
        return data.connected;
    } catch (error) {
        console.error(error);
        return false;
    }
}


async function sendMessage(textOverride) {
    const text = (textOverride !== undefined ? textOverride : input.value).trim();

    if (!text) {
        return;
    }

    addMessage(text, "user");

    if (textOverride === undefined) {
        input.value = "";
    }

    sendButton.disabled = true;

    try {
        const response = await fetch(
            `${API_BASE}/api/chat`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Session-Id": sessionId
                },
                body: JSON.stringify({
                    message: text,
                    session_id: sessionId
                })
            }
        );

        const data = await response.json();

        addMessage(data.reply, "bot");

        if (data.auth_required) {
            // Backend needs Google Calendar access. Remember the message so we
            // can retry it automatically once the user connects.
            pendingCalendarMessage = text;
            connectBanner.hidden = false;
        }

    } catch (error) {
        addMessage(
            "Could not connect to the chatbot server.",
            "bot"
        );

        console.error(error);

    } finally {
        sendButton.disabled = false;
        input.focus();
    }
}


function startGoogleAuth() {
    const url = `${API_BASE}/api/auth/google?session=${encodeURIComponent(sessionId)}`;
    // Open the OAuth flow in a popup; the callback page posts back a message.
    window.open(url, "google-oauth", "width=500,height=650");
}


// When the OAuth popup finishes it posts a message to this window.
window.addEventListener("message", async function (event) {
    if (event.data && event.data.type === "google-calendar-auth") {
        const connected = await refreshCalendarStatus();
        if (connected && pendingCalendarMessage) {
            const retry = pendingCalendarMessage;
            pendingCalendarMessage = null;
            addMessage("Google Calendar connected. Retrying...", "bot");
            sendMessage(retry);
        }
    }
});


sendButton.addEventListener("click", function () {
    sendMessage();
});

connectButton.addEventListener("click", startGoogleAuth);

input.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});


// Check connection state on load.
refreshCalendarStatus();
