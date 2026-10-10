# Manga Tracker

Personal manga/manhwa/manhua tracker for one owner (AniList user `porkhamhennessy`). Runs locally: FastAPI + SQLite backend, React + Vite + TypeScript frontend. Free only; no cloud, no paid APIs.

Design: [docs/design.md](docs/design.md). Plan and phases: [docs/PLAN.md](docs/PLAN.md). Read both before design decisions. Status log: [docs/STATUS.md](docs/STATUS.md); update it after each phase.

## Commands
- Run everything: `./run.sh` (`API_PORT=8765 ./run.sh` if 8000 is taken; port 8000 is often used by other local servers on this Mac)
- Backend setup: `cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- Backend tests: `cd backend && .venv/bin/pytest`
- Backend dev server: `cd backend && .venv/bin/uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm install && npm run dev` / `npm test` / `npm run build`

## Ground rules
- Work on a feature branch per phase (`feat/...`, `chore/...`), small commits, push the branch, one PR per phase. Never commit straight to `main`.
- Secrets live in `backend/.env` (gitignored, chmod 600): AniList client id/secret, Discord webhook, tokens. Never commit, log, print, or echo them. `.env.example` lists the keys with empty values.
- AniList: respect rate limits (90 req/min); cache, batch, and back off on 429. Never retry-loop on auth errors.
- External sources (MangaDex etc.) are behind the `ChapterSource` interface in `backend/app/sources/`. No scraping of sites that forbid it; prefer official APIs.
- Keep logic in plain modules under `backend/app/`; routes stay thin. Tests for every module; mock all network calls (no live calls in tests).
- Stay free: no paid services without asking.
