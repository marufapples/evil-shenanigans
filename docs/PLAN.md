# Plan

## Goal
One library for everything the owner reads. AniList is the source of truth for list and progress (two-way sync). The app adds automatic new-chapter detection, Discord alerts, and low-effort progress sync from reading sites.

## Architecture
- **Backend:** FastAPI, SQLAlchemy 2 + Alembic on SQLite (`backend/data/tracker.db`, gitignored), APScheduler for background jobs, httpx for all HTTP, pydantic-settings for config from `backend/.env`.
- **Frontend:** React + Vite + TypeScript, talks to the backend over JSON. Installable as a PWA later.
- **Layout:** `backend/app/{config,db,models,schemas,anilist,sources,notify,sync,scheduler,routes}`; `backend/tests/`; `frontend/src/`.

## Data model
- `manga`: id, anilist_id (unique), title, alt titles, cover, publishing status, total_chapters, mangadex_id (nullable), latest_known_chapter, updated_at
- `library_entry`: manga_id, list status (CURRENT/PLANNING/COMPLETED/PAUSED/DROPPED/REPEATING), progress, score, notes, started/completed, anilist_updated_at, local_updated_at, dirty flag (needs push)
- `chapter_event`: manga_id, chapter number, source, url, detected_at, notified flag
- `reading_site_link`: manga_id, site, url pattern (for progress sync)
- `oauth_token`: provider, access token, expiry (stored in DB, never logged)
- `sync_log`: job, started/finished, ok, message

## Phases (one branch + PR each)
0. `chore/project-setup`: CLAUDE.md, PLAN.md, .gitignore, config module, pytest scaffold, requirements cleanup.
1. `feat/library-db`: DB + Alembic, full AniList import of all list statuses, upsert, `/library` endpoints (filter/sort/search).
2. `feat/anilist-oauth`: OAuth login flow, token storage, push progress/status/score back to AniList, conflict rule: newer timestamp wins, dirty entries pushed on the next sync.
3. `feat/chapter-sources`: `ChapterSource` interface, MangaDex implementation, title matching AniList -> MangaDex (with manual override), new-chapter detection into `chapter_event`.
4. `feat/notifications`: Discord webhook notifier (new chapters grouped per tick, sync errors once), scheduler jobs with jitter, `/status` endpoint.
5. `feat/progress-sync`: `POST /progress` by reading-site URL, userscript/bookmarklet that reports the chapter being read, site-URL to manga mapping, one-click "mark next chapter read".
6. `feat/frontend-library`: library grid/list, filters, search, detail page, progress +1 button, unread-chapter badges.
7. `feat/frontend-settings`: AniList connect, source matching UI, sync status/log, notification test.
8. `chore/polish`: README, run script, error handling pass, PWA manifest, final test pass.
Owner extras are appended below as new phases.

## Risks / decisions
- AniList lacks chapter release data for most titles, hence MangaDex for new-chapter detection.
- Reading-site auto-sync can't scrape; userscript runs in the owner's own browser.
- Matching titles across sources is fuzzy; keep a manual override and never auto-merge low-confidence matches.

## Decision Log
See `docs/design.md`.
