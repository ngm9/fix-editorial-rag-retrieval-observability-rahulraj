#!/usr/bin/env bash
set -e

export DATABASE_URL="postgresql://courseuser:coursepass@localhost:5432/coursedb"

echo "[run] Starting pgvector container..."
docker-compose up -d

echo "[run] Waiting for database to be healthy..."
until docker-compose exec -T db pg_isready -U courseuser -d coursedb > /dev/null 2>&1; do
  echo "[run] Database not ready yet, waiting..."
  sleep 2
done
echo "[run] Database is healthy."

echo "[run] Installing Python dependencies..."
pip install -r requirements.txt

echo "[run] Applying schema and ingesting sample documents..."
python3 -m app.ingestion

echo "[run] Starting FastAPI application..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 5000 > uvicorn.log 2>&1 &
echo "[run] Server started. Logs in uvicorn.log"
