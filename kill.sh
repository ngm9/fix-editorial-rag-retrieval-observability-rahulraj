#!/usr/bin/env bash
docker-compose down -v
pkill -f uvicorn || true
echo "[kill] Services stopped."
