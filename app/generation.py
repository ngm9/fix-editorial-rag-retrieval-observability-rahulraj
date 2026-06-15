import logging
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger("editorial_rag.generation")

FALLBACK_ANSWER = "Insufficient evidence in the knowledge base to answer this question."
MODEL = "gpt-3.5-turbo"


def build_prompt(question: str, chunks: list[dict]) -> str:
    context_parts = []
    for i, chunk in enumerate(chunks):
        source = chunk.get("source", "unknown")
        text = chunk.get("chunk_text", "")
        context_parts.append(f"[{i+1}] Source: {source}\n{text}")

    context = "\n\n".join(context_parts)

    prompt = (
        f"You are an editorial research assistant. Answer the journalist's question "
        f"using only the context below. For each claim, cite the source label in brackets, "
        f"e.g. [1]. If the context does not contain enough information, say so explicitly.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer (with citations):"
    )
    return prompt


def extract_citations(chunks: list[dict]) -> list[str]:
    seen = set()
    citations = []
    for chunk in chunks:
        source = chunk.get("source", "")
        if source and source not in seen:
            seen.add(source)
            citations.append(source)
    return citations


def generate_answer(question: str, chunks: list[dict]) -> tuple[str, list[str]]:
    if not chunks:
        return FALLBACK_ANSWER, []

    prompt = build_prompt(question, chunks)
    citations = extract_citations(chunks)

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set; returning stub answer.")
        return "[LLM unavailable — no API key configured]", citations

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful editorial research assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    answer = response.choices[0].message.content or FALLBACK_ANSWER
    return answer, citations
