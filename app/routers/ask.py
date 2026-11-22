"""Grounded ask-SaansPlan route."""

import re

from fastapi import APIRouter, Request

from app.limiting import limiter
from app.models import AskRequest
from app.services.kb import KnowledgeBase

router = APIRouter()
kb = KnowledgeBase()


@router.post("/api/ask")
@limiter.limit("10/minute")
async def ask(request: Request, payload: AskRequest) -> dict[str, object]:
    """Retrieve grounded snippets or redirect unsafe medical requests."""
    question = payload.question.strip()
    if not question:
        return {
            "answer": "Please ask a short air-quality question.",
            "kb_ids": [],
            "safety_redirect": False,
        }
    text = question.lower()
    unsafe = any(
        term in text
        for term in ("dawa", "medicine", "dosage", "diagnose", "api key", "system prompt")
    )
    if unsafe:
        return {
            "answer": (
                "I cannot diagnose, prescribe medicine or reveal secrets. "
                "Consult a doctor for symptoms."
            ),
            "kb_ids": ["medical", "doctor"],
            "safety_redirect": True,
        }
    entries = kb.retrieve(question)
    answer = (
        " ".join(entry["text"] for entry in entries)
        or "No grounded entry matched. Use the engine's plan and consult a doctor for symptoms."
    )
    answer = re.sub(r"<[^>]*>", "", answer)
    return {
        "answer": answer[:900],
        "kb_ids": [entry["id"] for entry in entries],
        "safety_redirect": False,
    }
