import logging
import os

import psycopg
from dotenv import load_dotenv

from app.embeddings import embed_texts

load_dotenv()
logger = logging.getLogger("editorial_rag.retrieval")

SIMILARITY_THRESHOLD = 0.30


def retrieve_chunks(
    query: str,
    top_k: int = 5,
    source_filter: str | None = None,
) -> list[dict]:
    database_url = os.environ["DATABASE_URL"]
    query_embeddings = embed_texts([query])
    if not query_embeddings:
        return []
    query_vector = query_embeddings[0]

    results = []
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            if source_filter:
                cur.execute(
                    """
                    SELECT id, source, chunk_text, metadata,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM article_chunks
                    WHERE source = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (query_vector, source_filter, query_vector, top_k),
                )
            else:
                cur.execute(
                    """
                    SELECT id, source, chunk_text, metadata,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM article_chunks
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (query_vector, query_vector, top_k),
                )
            rows = cur.fetchall()

    for row in rows:
        chunk_id, source, chunk_text, metadata, similarity = row
        results.append({
            "id": chunk_id,
            "source": source,
            "chunk_text": chunk_text,
            "metadata": metadata,
            "similarity": float(similarity),
        })

    return results


def get_chunks_for_request(chunk_ids: list[int]) -> list[dict]:
    if not chunk_ids:
        return []
    database_url = os.environ["DATABASE_URL"]
    results = []
    with psycopg.connect(database_url) as conn:
        for chunk_id in chunk_ids:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, source, chunk_text, metadata FROM article_chunks WHERE id = %s",
                    (chunk_id,),
                )
                row = cur.fetchone()
                if row:
                    results.append({
                        "id": row[0],
                        "source": row[1],
                        "chunk_text": row[2],
                        "metadata": row[3],
                    })
    return results
