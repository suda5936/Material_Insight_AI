"""임베딩(Embeddings).

[수업 정리] RAG 파이프라인 2단계 = Embedding.
------------------------------------------------------------------
텍스트를 의미를 담은 고정 길이 벡터로 변환한다. 의미가 비슷한 문장은
벡터 공간에서 가깝게(코사인 유사도 높게) 위치한다.

LangChain 대응:
    from langchain_openai import OpenAIEmbeddings
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    vec = emb.embed_query("커튼월 자재 지연")       # 질의 1개
    vecs = emb.embed_documents([...])               # 문서 여러 개

아래 EmbeddingProvider(ABC)는 LangChain의 `Embeddings` 인터페이스를 직접 정의한 것:
    - embed_batch()  ↔ embed_documents()
    - embed_one()    ↔ embed_query()
인터페이스로 추상화했기 때문에 OpenAI를 vLLM 임베딩 등으로 교체하기 쉽다(전략 패턴).
테스트에서는 네트워크 없는 HashingEmbeddingProvider(가짜 구현)로 갈아끼운다.
"""

from abc import ABC, abstractmethod

import httpx

from app.core.config import get_settings


class EmbeddingProvider(ABC):
    """LangChain `Embeddings` 인터페이스에 해당하는 추상 베이스."""

    @property
    @abstractmethod
    def dimensions(self) -> int: ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...  # ↔ embed_documents

    async def embed_one(self, text: str) -> list[float]:  # ↔ embed_query
        results = await self.embed_batch([text])
        return results[0]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """LangChain의 OpenAIEmbeddings에 해당. /v1/embeddings 엔드포인트를 직접 호출한다."""

    def __init__(
        self,
        api_key: str,
        model: str,
        dimensions: int,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                f"{self._base_url}/embeddings",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "input": texts,
                    "dimensions": self._dimensions,
                },
            )
            response.raise_for_status()
            payload = response.json()

        ordered = sorted(payload["data"], key=lambda item: item["index"])
        return [item["embedding"] for item in ordered]


class EmbeddingProviderNotConfiguredError(Exception):
    pass


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if not settings.openai_api_key:
        raise EmbeddingProviderNotConfiguredError(
            "OPENAI_API_KEY is not configured; cannot create an embedding provider."
        )
    return OpenAIEmbeddingProvider(
        api_key=settings.openai_api_key,
        model=settings.openai_embedding_model,
        dimensions=settings.embedding_dimensions,
    )


def provide_embedding_provider() -> EmbeddingProvider:
    """FastAPI dependency entry point; override in tests via app.dependency_overrides."""
    return get_embedding_provider()
