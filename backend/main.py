from fastapi import FastAPI
from pydantic import BaseModel

from chatbot import chat


app = FastAPI()


class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
def send_message(request: ChatRequest):
    reply = chat(request.message)

    return {
        "reply": reply
    }