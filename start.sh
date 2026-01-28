#!/usr/bin/env bash
set -e

echo "Starting COC Server..."

# project root
cd /home/maruf/coc-server

# activate venv
source /home/maruf/coc-server/.venv/bin/activate

# start fastapi
echo "Starting FastAPI..."
uvicorn server:app --host 127.0.0.1 --port 8000 &

FASTAPI_PID=$!
echo "FastAPI PID: $FASTAPI_PID"

sleep 2

# start cloudflare tunnel
echo "Starting Cloudflare Tunnel..."
cloudflared tunnel --url http://127.0.0.1:8000 &

CF_PID=$!
echo "Cloudflare PID: $CF_PID"

echo "✅ Server started"
echo "Press Ctrl+C to stop"

wait
