from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence

import httpx

from app.core.config import Settings
from app.models.document import RetrievedDocument
from app.models.object import ReviewObjectRequest
from app.models.recommendation import RecommendationResult
from app.models.rule import RuleResult


class LLMClientError(RuntimeError):
    pass


class LLMClient(Protocol):
    def generate_recommendation(
        self,
        request: ReviewObjectRequest,
        rule_results: Sequence[RuleResult],
        sources: Sequence[RetrievedDocument],
        fallback: RecommendationResult,
    ) -> RecommendationResult:
        pass


@dataclass(frozen=True)
class MockLLMClient:
    def generate_recommendation(
        self,
        request: ReviewObjectRequest,
        rule_results: Sequence[RuleResult],
        sources: Sequence[RetrievedDocument],
        fallback: RecommendationResult,
    ) -> RecommendationResult:
        return fallback


@dataclass(frozen=True)
class OpenAIResponsesClient:
    api_key: str
    model: str
    timeout_seconds: float = 30.0

    def generate_recommendation(
        self,
        request: ReviewObjectRequest,
        rule_results: Sequence[RuleResult],
        sources: Sequence[RetrievedDocument],
        fallback: RecommendationResult,
    ) -> RecommendationResult:
        if not self.api_key:
            raise LLMClientError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")

        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": _user_prompt(request, rule_results, sources, fallback)},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "recommendation_result",
                    "schema": RecommendationResult.model_json_schema(),
                    "strict": True,
                }
            },
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                "https://api.openai.com/v1/responses",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
        return _parse_recommendation(_extract_responses_text(response.json()))


@dataclass(frozen=True)
class VLLMChatCompletionsClient:
    base_url: str
    model: str
    timeout_seconds: float = 30.0

    def generate_recommendation(
        self,
        request: ReviewObjectRequest,
        rule_results: Sequence[RuleResult],
        sources: Sequence[RetrievedDocument],
        fallback: RecommendationResult,
    ) -> RecommendationResult:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": _user_prompt(request, rule_results, sources, fallback)},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMClientError("vLLM response did not contain message content.") from exc
        return _parse_recommendation(content)


def build_llm_client(settings: Settings) -> LLMClient:
    provider = settings.llm_provider.lower().strip()
    if provider == "mock":
        return MockLLMClient()
    if provider == "openai":
        return OpenAIResponsesClient(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
    if provider == "vllm":
        return VLLMChatCompletionsClient(
            base_url=settings.vllm_base_url,
            model=settings.vllm_model,
        )
    raise LLMClientError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")


def _system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "recommendation_system.md"
    return prompt_path.read_text(encoding="utf-8").strip()


def _user_prompt(
    request: ReviewObjectRequest,
    rule_results: Sequence[RuleResult],
    sources: Sequence[RetrievedDocument],
    fallback: RecommendationResult,
) -> str:
    payload = {
        "instruction": (
            "Create a concise RecommendationResult JSON. Preserve recommendation_id, "
            "object_id, detected_issues, required_action, and sources from the fallback "
            "unless making the explanation more specific. Do not invent evidence."
        ),
        "review_object_request": request.model_dump(mode="json"),
        "rule_results": [result.model_dump(mode="json") for result in rule_results],
        "adopted_sources": [source.model_dump(mode="json") for source in sources],
        "fallback_result": fallback.model_dump(mode="json"),
    }
    return json.dumps(payload, ensure_ascii=False)


def _extract_responses_text(data: dict[str, Any]) -> str:
    if isinstance(data.get("output_text"), str):
        return data["output_text"]
    for output in data.get("output", []):
        for content in output.get("content", []):
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                return content["text"]
    raise LLMClientError("OpenAI response did not contain output text.")


def _parse_recommendation(content: str) -> RecommendationResult:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMClientError("LLM response was not valid JSON.") from exc
    return RecommendationResult.model_validate(payload)
