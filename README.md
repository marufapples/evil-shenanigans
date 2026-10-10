# Manga Tracker (evil-shenanigans)

A personal library for manga, manhwa and manhua. It syncs both ways with AniList, detects new chapters through MangaDex, sends them to Discord, and moves your progress forward automatically while you read on other sites.

## Run it

```bash
cp backend/.env.example backend/.env   # then fill it in (first time only)
./run.sh
```

Open http://localhost:5173. The API runs on http://localhost:8765.

## First-time setup
1. **AniList app:** at https://anilist.co/settings/developer, set the redirect URI to `http://localhost:8765/auth/anilist/callback`. Put the client id/secret in `backend/.env`.
2. **Connect:** Settings → *Connect AniList*, approve, and you're back in the app.
3. **Import:** Settings → *Import from AniList now* (it also runs every 30 minutes).
4. **Reading-site sync (optional):** install Tampermonkey, then open Settings → *the userscript*. Opening a chapter page on any site reports it. The first time a site is seen, the series is matched by title; after that, by URL.
5. **Discord:** set `DISCORD_WEBHOOK_URL`, then Settings → *Send test Discord message*.

## How it works
- **Library:** AniList is the source of truth. Edits made here are marked *dirty* and pushed to AniList; imports never overwrite unpushed edits.
- **New chapters:** series you're reading (`CURRENT`/`REPEATING`, still releasing) are matched to MangaDex (exact AniList link, else a ≥95% title match). The first check only records a baseline, and later increases create an alert. Series that aren't found can be linked by hand in Settings.
- **Jobs:** import every 30 min, push every 10 min, chapter check every 30 min, all with jitter. A failing job alerts Discord once per failure streak.

## Development
```bash
cd backend && .venv/bin/pytest
cd frontend && npm test && npm run build
```
Plan: [docs/PLAN.md](docs/PLAN.md) · Status: [docs/STATUS.md](docs/STATUS.md) · Conventions: [CLAUDE.md](CLAUDE.md)
