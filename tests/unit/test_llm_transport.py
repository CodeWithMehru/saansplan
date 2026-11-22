"""Groq transport edge tests."""

import pytest

from app.services import llm


@pytest.mark.asyncio
async def test_groq_chat_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        await llm.groq_chat("system", "user", 0.1)


@pytest.mark.asyncio
async def test_groq_chat_empty_choices(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"choices": []}

    class MockClient:
        async def __aenter__(self) -> "MockClient":
            return self

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

        async def post(self, *args: object, **kwargs: object) -> MockResponse:
            return MockResponse()

    monkeypatch.setenv("GROQ_API_KEY", "test-placeholder-not-a-secret")
    monkeypatch.setattr(llm.httpx, "AsyncClient", lambda timeout: MockClient())
    with pytest.raises(RuntimeError):
        await llm.groq_chat("system", "user", 0.1)
