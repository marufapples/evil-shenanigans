# Status

- Phase 0 `chore/project-setup`: done (pushed).
- Phase 1 `feat/library-db`: done. SQLite + Alembic, full AniList import (33 entries verified live), `/library` list/filter/search/sort, `/library/import`. Branch is stacked on phase 0.
- Note: AniList username is `porkhamhennessy` (`porkhamsandwich` is the API client name, not a user).
- Phase 2 `feat/anilist-oauth`: done (stacked on phase 1). OAuth login/callback/status/logout, PATCH /library/{id} marks dirty + pushes to AniList, POST /library/push retries. **Owner action:** open http://localhost:8000/auth/anilist/login once to authorize (consent cannot be done unattended). Redirect URI in the AniList developer settings must be exactly `http://localhost:8000/auth/anilist/callback`.
