import pytest

from app.services.chunking import chunk_text


def test_chunk_text_uses_default_size_and_overlap() -> None:
    text = "a" * 3000

    chunks = chunk_text(text)

    assert len(chunks[0]) == 1200
    assert len(chunks) == 3
    # stride is size - overlap = 1000, so chunk 2 starts at offset 1000
    assert chunks[1] == text[1000:2200]


def test_chunk_text_covers_full_text_with_short_input() -> None:
    text = "short document body"

    chunks = chunk_text(text, chunk_size=1200, overlap=200)

    assert chunks == [text]


def test_chunk_text_empty_returns_no_chunks() -> None:
    assert chunk_text("   ") == []


def test_chunk_text_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError):
        chunk_text("hello world", chunk_size=10, overlap=10)


def test_chunk_text_custom_size_and_overlap() -> None:
    text = "0123456789" * 3  # 30 chars

    chunks = chunk_text(text, chunk_size=10, overlap=4)

    assert chunks[0] == text[0:10]
    assert chunks[1] == text[6:16]
    assert chunks[-1][-1] == text[-1]
