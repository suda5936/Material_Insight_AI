from app.services.embedding_client import LocalHashEmbeddingClient, vector_to_pg_literal


def test_local_hash_embedding_is_deterministic_and_normalized() -> None:
    client = LocalHashEmbeddingClient(dimensions=8)

    first = client.embed_text("interior wall meeting room acoustic")
    second = client.embed_text("interior wall meeting room acoustic")

    assert first == second
    assert len(first) == 8
    assert any(value != 0 for value in first)
    assert vector_to_pg_literal(first).startswith("[")
    assert vector_to_pg_literal(first).endswith("]")
