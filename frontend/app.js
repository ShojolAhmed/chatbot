const input = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const messages = document.getElementById("messages");


function addMessage(text, sender) {
    const message = document.createElement("div");

    message.classList.add("message");
    message.classList.add(sender);

    message.textContent = text;

    messages.appendChild(message);

    messages.scrollTop = messages.scrollHeight;
}


async function sendMessage() {
    const text = input.value.trim();

    if (!text) {
        return;
    }

    addMessage(text, "user");

    input.value = "";

    sendButton.disabled = true;

    try {
        const response = await fetch(
            "http://127.0.0.1:8000/api/chat",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: text
                })
            }
        );

        const data = await response.json();

        addMessage(data.reply, "bot");

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


sendButton.addEventListener("click", sendMessage);


input.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});