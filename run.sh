#!/usr/bin/env bash
# Start the backend API and the frontend dev server together. Ctrl-C stops both.
# API_PORT defaults to 8765. If you change it, also change ANILIST_REDIRECT_URI in backend/.env
# and the redirect URL of your AniList API client to http://localhost:$API_PORT/auth/anilist/callback.
set -euo pipefail
cd "$(dirname "$0")"
API_PORT="${API_PORT:-8765}"

if [ ! -x backend/.venv/bin/uvicorn ]; then
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install -q -r backend/requirements.txt
fi
if lsof -nP -iTCP:"$API_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port $API_PORT is already in use by another program:" >&2
  lsof -nP -iTCP:"$API_PORT" -sTCP:LISTEN >&2
  echo "Stop it, or run with a different port: API_PORT=<port> ./run.sh" >&2
  exit 1
fi
[ -d frontend/node_modules ] || (cd frontend && npm install)

trap 'kill 0' EXIT
(cd backend && .venv/bin/uvicorn app.main:app --port "$API_PORT") &
(cd frontend && VITE_API_URL="http://localhost:$API_PORT" npm run dev -- --port 5173) &
wait
