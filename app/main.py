import logging
import os
import uuid
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.generation import generate_answer
from app.retrieval import retrieve_chunks, get_chunks_for_request

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("editorial_rag")

app = FastAPI(title="Editorial Research Assistant")


class ResearchRequest(BaseModel):
    question: str
    top_k: int = 5


class ResearchResponse(BaseModel):
    request_id: str
    answer: str
    citations: list[str]


class DebugChunk(BaseModel):
    chunk_id: int
    source: str
    chunk_text: str
    similarity: float | None = None


class DebugResponse(BaseModel):
    request_id: str
    chunks: list[DebugChunk]
    page: int
    page_size: int
    total: int


_request_store: dict[str, list[dict]] = {}


@app.post("/api/research/answer", response_model=ResearchResponse)
def answer_research_question(body: ResearchRequest):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    request_id = str(uuid.uuid4())

    chunks = retrieve_chunks(body.question, top_k=body.top_k)

    answer, citations = generate_answer(body.question, chunks)

    _request_store[request_id] = chunks

    return ResearchResponse(
        request_id=request_id,
        answer=answer,
        citations=citations,
    )


@app.get("/internal/rag/debug", response_model=DebugResponse)
def debug_request(
    request_id: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    if request_id not in _request_store:
        raise HTTPException(status_code=404, detail="Request ID not found.")

    all_chunks = _request_store[request_id]
    total = len(all_chunks)
    start = (page - 1) * page_size
    end = start + page_size
    page_chunks = all_chunks[start:end]

    debug_chunks = [
        DebugChunk(
            chunk_id=c.get("id", 0),
            source=c.get("source", ""),
            chunk_text=c.get("chunk_text", ""),
            similarity=c.get("similarity"),
        )
        for c in page_chunks
    ]

    return DebugResponse(
        request_id=request_id,
        chunks=debug_chunks,
        page=page,
        page_size=page_size,
        total=total,
    )
