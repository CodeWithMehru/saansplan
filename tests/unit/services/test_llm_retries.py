"""LLM transport retry and validation tests."""

from __future__ import annotations

import pytest

from app.services import llm


@pytest.mark.asyncio
async def test_explanation_retries_then_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify invalid LLM output triggers retries and falls back to template."""
    calls = 0

    async def bad_chat(*args: object, **kwargs: object) -> str:
        nonlocal calls
        calls += 1
        return '{"text":"45% lower"}'

    monkeypatch.setattr(llm, "groq_chat", bad_chat)
    result = await llm.explain_with_fallback(
        {"peak_hour": 18, "peak_aqi": 312, "top_swap": {"percent_reduction": 29}, "hourly": []},
        "en",
    )
    assert calls == 2
    assert result["ai_available"] is False


@pytest.mark.asyncio
async def test_parse_empty_text_rejected() -> None:
    """Verify empty or whitespace routine text is rejected."""
    with pytest.raises(ValueError):
        await llm.parse_routine("   ")
