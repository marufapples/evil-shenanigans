# Status

- Phase 0 `chore/project-setup`: done (pushed).
- Phase 1 `feat/library-db`: done. SQLite + Alembic, full AniList import (33 entries verified live), `/library` list/filter/search/sort, `/library/import`. Branch is stacked on phase 0.
- Note: AniList username is `porkhamhennessy` (`porkhamsandwich` is the API client name, not a user).
- Phase 2 `feat/anilist-oauth`: done (stacked on phase 1). OAuth login/callback/status/logout, PATCH /library/{id} marks dirty + pushes to AniList, POST /library/push retries. **Owner action:** open http://localhost:8000/auth/anilist/login once to authorize (consent cannot be done unattended). Redirect URI in the AniList developer settings must be exactly `http://localhost:8000/auth/anilist/callback`.
- Phase 3 `feat/chapter-sources`: done (stacked). MangaDex source, exact AniList-link matching (fuzzy >=95 fallback), baseline-then-alert detection, /chapters/check and /chapters/events. Live: 23/33 matched, 10 have English chapters on MangaDex (others licensed/off-MangaDex; more sources are a future phase).
- Phase 4 `feat/notifications`: done (stacked). Discord notifier (batched, marked sent only on success), APScheduler jobs with jitter (import 30m, push 10m, chapters 30m), one alert per failure streak, /status, /notify/test (verified live: test message delivered).
- Phase 5 `feat/progress-sync`: done (stacked). POST /progress (token-protected), site-URL -> manga links learned automatically, forward-only updates, Tampermonkey userscript at GET /progress/userscript, bookmarklet-style GET /progress/report. Owner action: install the userscript from http://localhost:8000/progress/userscript in Tampermonkey.
