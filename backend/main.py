import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("BASE_URL"),
    # AgentRouter Specific: Allowlisted Client
    default_headers={
        "User-Agent": os.getenv(
            "CLIENT_USER_AGENT", "claude-cli/1.0.83 (external, cli)"
        )
    },
)


completion = client.chat.completions.create(
    model="claude-opus-4-8",
    messages=[
        {"role": "system", "content": "You're a helpful assistant."},
        {
            "role": "user",
            "content": "Greet me in one sentence.",
        },
    ],
)

response = completion.choices[0].message.content
print(response)
