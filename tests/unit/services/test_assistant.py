"""Unit tests for app.services.assistant module."""

from __future__ import annotations

import pytest

from app.services.assistant import _parse_assistant_response, answer_question
from app.services.assistant_grounding import _fallback_walk


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


def test_parse_assistant_response_invalid_json() -> None:
    """Malformed LLM response returns None without throwing."""
    assert _parse_assistant_response("invalid json", []) is None


def test_fallback_walk_without_info() -> None:
    """Fallback walk message handles missing walk_info gracefully."""
    res = _fallback_walk(18, None, "Delhi")
    assert "check local aqi" in res["answer"].lower()


def test_assistant_hour_and_cadr_resolvers() -> None:
    """Verify 12am clock extraction, Hindi phrases, CADR insertion, and CPCB ensure."""
    from app.services.assistant import (
        _ensure_cpcb_breakpoint_entry,
        _is_valid_hour,
        extract_hour,
        resolve_cadr,
    )

    assert extract_hour("walk at 12am") == 0
    assert extract_hour("subah 6 baje") == 6
    assert extract_hour("dopahar 12 baje") == 12

    entries: list[dict[str, str]] = [{"id": "other-id", "content": "text"}]
    _, cfm = resolve_cadr(150.0, entries)
    assert cfm == 100
    assert any(e["id"] == "purifier-sizing" for e in entries)

    assert _is_valid_hour(-1, 24) is False
    assert _is_valid_hour(24, 24) is False
    assert _is_valid_hour(12, 24) is True

    empty_entries: list[dict[str, str]] = []
    _ensure_cpcb_breakpoint_entry(empty_entries)
    assert any(e["id"] == "cpcb-aqi-breakpoints" for e in empty_entries)


@pytest.mark.asyncio
async def test_assistant_deterministic_fallbacks_on_groq_failure() -> None:
    """Verify answer_question falls back deterministically when Groq chat fails."""
    from unittest.mock import AsyncMock, patch

    from app.services.assistant import answer_question

    with patch("app.services.assistant.groq_chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = RuntimeError("Groq API error")
        with patch("app.services.assistant.fetch_air_quality", new_callable=AsyncMock) as mock_aq:
            mock_aq.return_value = {
                "pm25": [150.0] * 24,
                "aqi": [220] * 24,
                "times": ["T"] * 24,
                "timezone": "Asia/Kolkata",
            }
            resp = await answer_question(
                "purifier for 150 sq ft room", location=(28.6, 77.2, "Delhi")
            )
            assert "100 CFM" in resp["answer"]
            assert resp["safety_redirect"] is False

            resp_walk = await answer_question("can I walk at 6 pm?", location=(28.6, 77.2, "Delhi"))
            assert resp_walk["safety_redirect"] is False
            assert "AQI" in resp_walk["answer"]


@pytest.mark.asyncio
async def test_assistant_and_resolver_edge_cases() -> None:
    """Verify assistant helper fallbacks and resolver edge cases."""
    from unittest.mock import AsyncMock, MagicMock

    from app.services import assistant, assistant_grounding
    from app.services.kb import KnowledgeBase

    res = await assistant.answer_question("")
    assert "Please ask" in res["answer"]

    mock_fetch = AsyncMock(return_value={"pm25": "invalid"})
    pm25 = await assistant._fetch_today_pm25(28.6, 77.2, None, mock_fetch)
    assert pm25 == []

    empty_chat = AsyncMock(return_value='{"answer": "   ", "kb_ids": []}')
    res_groq = await assistant._call_groq_assistant("question", {}, [], empty_chat)
    assert res_groq is None

    h = assistant_grounding._extract_12h_hour("at 9 am")
    assert h == 9

    mock_kb = MagicMock(spec=KnowledgeBase)
    mock_kb.entries = []
    entries: list[dict[str, object]] = []
    assistant_grounding._attach_cadr_kb_entry(entries, mock_kb)
    assert len(entries) == 0
    assistant_grounding._ensure_cpcb_breakpoint_entry(entries, mock_kb)
    assert len(entries) == 0
