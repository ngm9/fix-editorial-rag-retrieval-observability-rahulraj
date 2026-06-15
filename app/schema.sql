CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS article_chunks (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(384)
);

CREATE INDEX IF NOT EXISTS article_chunks_embedding_idx
    ON article_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE TABLE IF NOT EXISTS request_log (
    id SERIAL PRIMARY KEY,
    request_id TEXT NOT NULL,
    question TEXT NOT NULL,
    retrieval_ms FLOAT,
    generation_ms FLOAT,
    prompt_tokens INTEGER,
    chunk_ids INTEGER[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);
