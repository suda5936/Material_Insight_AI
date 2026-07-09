import httpx
import pytest

from app.services.llm.openai_compatible import OpenAICompatibleProvider
from app.services.llm.types import LLMMessage, LLMProviderError


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)  # type: ignore[arg-type]

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    def __init__(self, response: _FakeResponse, captured_calls: list) -> None:
        self._response = response
        self._captured_calls = captured_calls

    async def __aenter__(self) -> "_FakeClient":
        return self

    async def __aexit__(self, *exc_info: object) -> bool:
        return False

    async def post(self, url: str, headers: dict, json: dict) -> _FakeResponse:
        self._captured_calls.append({"url": url, "headers": headers, "json": json})
        return self._response


async def test_complete_returns_content_from_chat_completions_response(monkeypatch) -> None:
    captured: list = []
    response = _FakeResponse({"choices": [{"message": {"content": "hello"}}]})
    monkeypatch.setattr(
        "app.services.llm.openai_compatible.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeClient(response, captured),
    )

    provider = OpenAICompatibleProvider(
        name="test-provider", base_url="http://localhost:9000/v1", model="test-model", api_key="secret"
    )
    result = await provider.complete([LLMMessage(role="user", content="hi")], temperature=0.2)

    assert result.content == "hello"
    assert result.model == "test-model"
    assert result.provider_name == "test-provider"
    assert captured[0]["url"] == "http://localhost:9000/v1/chat/completions"
    assert captured[0]["headers"]["Authorization"] == "Bearer secret"
    assert captured[0]["json"]["temperature"] == 0.2


async def test_complete_without_api_key_omits_auth_header(monkeypatch) -> None:
    captured: list = []
    response = _FakeResponse({"choices": [{"message": {"content": "hi"}}]})
    monkeypatch.setattr(
        "app.services.llm.openai_compatible.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeClient(response, captured),
    )

    provider = OpenAICompatibleProvider(name="vllm", base_url="http://localhost:8000/v1", model="qwen")
    await provider.complete([LLMMessage(role="user", content="hi")])

    assert "Authorization" not in captured[0]["headers"]


async def test_complete_raises_llm_provider_error_on_http_failure(monkeypatch) -> None:
    response = _FakeResponse({}, status_code=500)
    monkeypatch.setattr(
        "app.services.llm.openai_compatible.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeClient(response, []),
    )

    provider = OpenAICompatibleProvider(name="test-provider", base_url="http://x", model="m")

    with pytest.raises(LLMProviderError):
        await provider.complete([LLMMessage(role="user", content="hi")])


async def test_complete_raises_llm_provider_error_on_malformed_payload(monkeypatch) -> None:
    response = _FakeResponse({"unexpected": "shape"})
    monkeypatch.setattr(
        "app.services.llm.openai_compatible.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeClient(response, []),
    )

    provider = OpenAICompatibleProvider(name="test-provider", base_url="http://x", model="m")

    with pytest.raises(LLMProviderError):
        await provider.complete([LLMMessage(role="user", content="hi")])
