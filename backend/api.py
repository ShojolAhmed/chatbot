import logging

from fastapi import APIRouter, HTTPException
from openai import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)
from pydantic import BaseModel

from .chatbot import chat

router = APIRouter()

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str


@router.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    try:
        response = chat(request.message)
        return {"response": response}

    except AuthenticationError:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key.",
        )

    except BadRequestError:
        raise HTTPException(
            status_code=400,
            detail="Invalid request sent to the AI service.",
        )

    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="API rate limit exceeded.",
        )

    except APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to the AI service.",
        )

    except APIError:
        raise HTTPException(
            status_code=502,
            detail="AI service returned an error.",
        )

    except Exception:
        logger.exception("Unexpected error in /api/chat")
        raise HTTPException(
            status_code=500,
            detail="An unexpected server error occurred.",
        )
