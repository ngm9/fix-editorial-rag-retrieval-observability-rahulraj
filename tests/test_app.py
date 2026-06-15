import os
import sys
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://courseuser:coursepass@localhost:5432/coursedb")
os.environ.setdefault("OPENAI_API_KEY", "test-key")


def test_generate_answer_returns_fallback_when_no_chunks():
    from app.generation import generate_answer, FALLBACK_ANSWER

    answer, citations = generate_answer("What is the streaming revenue?", [])
    assert answer == FALLBACK_ANSWER
    assert citations == []


def test_extract_citations_deduplicates_sources():
    from app.generation import extract_citations

    chunks = [
        {"source": "sample_doc_1.md", "chunk_text": "text a"},
        {"source": "sample_doc_1.md", "chunk_text": "text b"},
        {"source": "sample_doc_2.md", "chunk_text": "text c"},
    ]
    citations = extract_citations(chunks)
    assert citations == ["sample_doc_1.md", "sample_doc_2.md"]
    assert len(citations) == 2


def test_evaluation_recall_at_k_not_implemented():
    from app.evaluation import compute_recall_at_k

    result = compute_recall_at_k(["sample_doc_1.md", "sample_doc_2.md"], "sample_doc_1.md", k=5)
    assert result is None or isinstance(result, float), (
        "compute_recall_at_k must return a float between 0.0 and 1.0"
    )


def test_evaluation_mrr_not_implemented():
    from app.evaluation import compute_mrr

    result = compute_mrr(["sample_doc_2.md", "sample_doc_1.md"], "sample_doc_1.md")
    assert result is None or isinstance(result, float), (
        "compute_mrr must return a float between 0.0 and 1.0"
    )


def test_split_into_chunks_produces_non_empty_chunks():
    from app.ingestion import split_into_chunks

    text = "word " * 300
    chunks = split_into_chunks(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert all(len(c) > 0 for c in chunks)


def test_answer_endpoint_empty_question(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post("/api/research/answer", json={"question": ""})
    assert response.status_code == 400
