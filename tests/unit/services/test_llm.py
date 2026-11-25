"""Unit tests for app.services.llm module."""

from __future__ import annotations

import pytest

from app.services.llm import explain_with_fallback, parse_routine


@pytest.mark.asyncio
async def test_parse_routine_raises_on_llm_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """When LLM call fails, parse_routine raises RuntimeError."""

    async def mock_fail(*args: object, **kwargs: object) -> str:
        raise RuntimeError("Groq unreachable")

    monkeypatch.setattr("app.services.llm.groq_chat", mock_fail)
    with pytest.raises(RuntimeError):
        await parse_routine("subah 7 baje walk")


@pytest.mark.asyncio
async def test_explain_with_fallback_serves_templated_on_guard_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When LLM produces hallucinated numbers or fails, return deterministic fallback."""

    async def mock_fail(*args: object, **kwargs: object) -> str:
        raise RuntimeError("Groq down")

    monkeypatch.setattr("app.services.llm.groq_chat", mock_fail)
    engine = {
        "peak_hour": 18,
        "peak_aqi": 250,
        "cleaner_day": {
            "percent_reduction": 30.0,
            "inhaled_saved_ug": 300.0,
            "inhaled_saved_range_ug": [225.0, 375.0],
        },
    }
    result = await explain_with_fallback(engine, language="en")
    assert result is not None
    assert result.explanation != ""
    assert "30" in result.explanation
    assert result.ai_available is False
