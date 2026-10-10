#!/usr/bin/env bash
# Start the backend API and the frontend dev server together. Ctrl-C stops both.
# API_PORT defaults to 8000; if it's taken, run e.g. `API_PORT=8765 ./run.sh`
# (and set the AniList redirect URI to http://localhost:$API_PORT/auth/anilist/callback).
set -euo pipefail
cd "$(dirname "$0")"
API_PORT="${API_PORT:-8000}"

if [ ! -x backend/.venv/bin/uvicorn ]; then
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install -q -r backend/requirements.txt
fi
[ -d frontend/node_modules ] || (cd frontend && npm install)

trap 'kill 0' EXIT
(cd backend && .venv/bin/uvicorn app.main:app --port "$API_PORT") &
(cd frontend && VITE_API_URL="http://localhost:$API_PORT" npm run dev -- --port 5173) &
wait
