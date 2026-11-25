"""Unit tests for app.services.assistant module."""

from __future__ import annotations

import pytest

from app.services.assistant import answer_question


@pytest.mark.asyncio
async def test_answer_question_safety_intercept() -> None:
    """Medical symptom queries must be intercepted deterministically without LLM."""
    res = await answer_question("I have chest pain and shortness of breath")
    assert "doctor" in res["answer"].lower() or "medical" in res["answer"].lower()
    assert res.get("safety_redirect") is True


@pytest.mark.asyncio
async def test_answer_question_purifier_intent() -> None:
    """Purifier sizing questions must trigger CADR resolution."""
    res = await answer_question("How much CADR do I need for 150 sq ft room?")
    assert (
        "cadr" in res["answer"].lower()
        or "m³/h" in res["answer"].lower()
        or "smoke" in res["answer"].lower()
    )
