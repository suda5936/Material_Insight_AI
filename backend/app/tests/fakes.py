from app.services.embeddings import EmbeddingProvider
from app.services.llm.types import LLMMessage, LLMProvider, LLMProviderError, LLMResponse


class HashingEmbeddingProvider(EmbeddingProvider):
    """Deterministic, network-free embedding provider for tests.

    Uses word-level feature hashing so that texts sharing keywords produce
    similar vectors, giving retrieval ranking tests meaningful signal.
    """

    def __init__(self, dimensions: int = 1536) -> None:
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        for word in text.lower().split():
            index = hash(word) % self._dimensions
            vector[index] += 1.0
        return vector


class FakeLLMProvider(LLMProvider):
    """Canned-response provider for tests; never touches the network."""

    def __init__(self, name: str = "fake", response_content: str = "{}", fail: bool = False) -> None:
        self.name = name
        self._response_content = response_content
        self._fail = fail
        self.calls: list[list[LLMMessage]] = []

    async def complete(self, messages: list[LLMMessage], temperature: float = 0.0) -> LLMResponse:
        self.calls.append(messages)
        if self._fail:
            raise LLMProviderError(f"{self.name} was configured to fail.")
        return LLMResponse(content=self._response_content, model="fake-model", provider_name=self.name)


def build_fake_registry(mapping: str = "{}", plan: str = "{}", review: str = "{}"):
    """Registry wired with canned JSON per role for orchestrator/E2E tests."""
    from app.services.llm.registry import LLMProviderRegistry
    from app.services.llm.types import LLMRole

    return LLMProviderRegistry(
        {
            LLMRole.ISSUE_MAPPER: FakeLLMProvider(name="fake-gemma-mapper", response_content=mapping),
            LLMRole.RECOVERY_PLANNER: FakeLLMProvider(name="fake-openai", response_content=plan),
            LLMRole.REVIEWER: FakeLLMProvider(name="fake-gemma", response_content=review),
        },
        {},
    )
