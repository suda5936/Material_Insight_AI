"""OpenAI 호환 Chat 어댑터.

[수업 정리] LangChain의 ChatOpenAI / 커스텀 ChatModel 구현.
------------------------------------------------------------------
LangChain 대응:
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(base_url=..., model=..., api_key=...)   # OpenAI
    llm = ChatOpenAI(base_url="http://vllm:8000/v1", ...)     # vLLM도 동일 스키마!

핵심 포인트: OpenAI와 vLLM은 둘 다 `/v1/chat/completions` 스키마를 따르므로
"하나의 어댑터"로 두 백엔드를 모두 호출할 수 있다. 그래서 이 클래스 하나로
OpenAI(Planner)와 vLLM(Mapper/Reviewer)을 전부 커버한다.
"""

import httpx

from app.services.llm.types import LLMMessage, LLMProvider, LLMProviderError, LLMResponse


class OpenAICompatibleProvider(LLMProvider):
    """LangChain ChatOpenAI 에 해당. OpenAI와 vLLM(OpenAI 호환) 모두 지원.

    Chat-completions adapter shared by OpenAI and any OpenAI-compatible
    server (vLLM's `/v1/chat/completions` endpoint speaks the same schema)."""

    def __init__(
        self,
        name: str,
        base_url: str,
        model: str,
        api_key: str = "",
        timeout_seconds: float = 30.0,
    ) -> None:
        self.name = name
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.0,
    ) -> LLMResponse:
        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": self._model,
                        "temperature": temperature,
                        "messages": [
                            {"role": message.role, "content": message.content} for message in messages
                        ],
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"{self.name} request failed: {exc}") from exc

        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMProviderError(f"{self.name} returned an unexpected response shape.") from exc

        return LLMResponse(content=content, model=self._model, provider_name=self.name)
