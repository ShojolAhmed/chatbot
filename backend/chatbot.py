import os

from dotenv import load_dotenv
from openai import OpenAI

from .memory import add_message, get_messages

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL = "claude-opus-4-8"

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    # AgentRouter Specific: Allowlisted Client
    default_headers={
        "User-Agent": os.getenv("CLIENT_USER_AGENT"),
    },
)


def chat(message: str) -> str:
    add_message("user", message)

    messages = [
        {
            "role": "system",
            "content": "You're a helpful assistant.",
        },
        *get_messages(),
    ]

    completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )

    response = completion.choices[0].message.content
    add_message("assistant", response)
    return response
