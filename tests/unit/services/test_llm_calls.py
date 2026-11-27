import pytest

from app.services import llm


@pytest.mark.asyncio
async def test_parse_routine_with_mock(monkeypatch):
    raw = (
        '{"activities":[{"label":"Walk","start_hour":17,"duration_min":30,'
        '"place":"outdoor","mode":"walk","intensity":"moderate","member_refs":[0]}],'
        '"home":{"heating":"none","cooking":"lpg","windows":"mostly_closed",'
        '"purifier":false,"has_chimney":false},"unclear":[]}'
    )

    async def mock_chat(*args, **kwargs):
        return raw

    monkeypatch.setattr(llm, "groq_chat", mock_chat)
    routine = await llm.parse_routine("I walk at 5 pm")
    assert routine.activities[0].start_hour == 17


@pytest.mark.asyncio
async def test_explanation_accepts_valid_engine_text(monkeypatch):
    async def mock_chat(*args, **kwargs):
        return "Exposure may be 29% lower and AQI may reach 312."

    monkeypatch.setattr(llm, "groq_chat", mock_chat)
    engine = {"peak_hour": 18, "peak_aqi": 312, "top_swap": {"percent_reduction": 29}, "hourly": []}
    result = await llm.explain_with_fallback(engine, "en")
    assert result["ai_available"] is True


@pytest.mark.asyncio
async def test_explanation_retries_unknown_number(monkeypatch):
    calls = 0

    async def mock_chat(*args, **kwargs):
        nonlocal calls
        calls += 1
        return "Exposure may be 45% lower."

    monkeypatch.setattr(llm, "groq_chat", mock_chat)
    engine = {"peak_hour": 18, "peak_aqi": 312, "top_swap": {"percent_reduction": 29}, "hourly": []}
    result = await llm.explain_with_fallback(engine, "en")
    assert calls == 2
    assert result["ai_available"] is False
