import json
import logging
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from app.embeddings import embed_texts

load_dotenv()
logger = logging.getLogger("editorial_rag.ingestion")

DATA_DIR = Path(__file__).parent.parent / "data"
CHUNK_SIZE = 400
CHUNK_OVERLAP = 60


def load_markdown_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start += chunk_size - overlap
    return [c for c in chunks if c]


def apply_schema(conn: psycopg.Connection) -> None:
    schema_path = Path(__file__).parent / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()


def ingest_documents() -> None:
    database_url = os.environ["DATABASE_URL"]
    doc_paths = list(DATA_DIR.glob("*.md"))

    if not doc_paths:
        logger.warning("No markdown documents found in %s", DATA_DIR)
        return

    with psycopg.connect(database_url) as conn:
        apply_schema(conn)

        for doc_path in doc_paths:
            source = doc_path.name
            text = load_markdown_file(doc_path)
            chunks = split_into_chunks(text)

            logger.info("Ingesting %s: %d chunks", source, len(chunks))

            embeddings = embed_texts(chunks)

            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM article_chunks WHERE source = %s",
                    (source,),
                )
                row = cur.fetchone()
                existing_count = row[0] if row else 0

            if existing_count > 0:
                logger.info("Source %s already ingested, skipping.", source)
                continue

            with conn.cursor() as cur:
                for chunk_text, embedding in zip(chunks, embeddings):
                    metadata = {"source": source}
                    cur.execute(
                        """
                        INSERT INTO article_chunks (source, chunk_text, metadata, embedding)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (source, chunk_text, json.dumps(metadata), embedding),
                    )
            conn.commit()
            logger.info("Committed %d chunks for %s", len(chunks), source)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ingest_documents()
