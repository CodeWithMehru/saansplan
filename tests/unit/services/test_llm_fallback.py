import pytest

from app.services import llm


@pytest.mark.asyncio
async def test_groq_down_returns_fallback(monkeypatch):
    async def unavailable(*args, **kwargs):
        raise RuntimeError("Groq unavailable")

    monkeypatch.setattr(llm, "groq_chat", unavailable)
    engine = {"peak_hour": 18, "peak_aqi": 312, "top_swap": {"percent_reduction": 29}, "hourly": []}
    result = await llm.explain_with_fallback(engine, "hinglish")
    assert result["ai_available"] is False
    assert "312" in result["explanation"]
