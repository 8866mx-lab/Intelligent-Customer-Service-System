"""Tests for knowledge base ingest helpers."""

from src.services.kb_ingest import EMBEDDING_BATCH_SIZE, KbIngestService


def test_embedding_batch_size_within_dashscope_limit():
    assert EMBEDDING_BATCH_SIZE <= 10


def test_split_chunks_splits_long_paragraph():
    service = KbIngestService(repo=None)  # type: ignore[arg-type]
    text = "x" * 2000
    chunks = service._split_chunks(text, chunk_size=512)

    assert len(chunks) >= 4
    assert all(len(chunk) <= 512 for chunk in chunks)


def test_split_chunks_preserves_short_paragraphs():
    service = KbIngestService(repo=None)  # type: ignore[arg-type]
    text = "第一段\n\n第二段\n\n第三段"
    chunks = service._split_chunks(text, chunk_size=512)

    assert len(chunks) >= 1
    assert "第一段" in chunks[0]
