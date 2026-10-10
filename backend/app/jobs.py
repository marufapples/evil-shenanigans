import logging

from app.anilist import fetch_library
from app.config import get_settings
from app.db import SessionLocal
from app.detect import detect_new_chapters
from app.importer import upsert_library
from app.notify import notify_new_chapters, send_discord
from app.sources.mangadex import MangaDexSource
from app.sync import push_dirty
from app.timeutil import utcnow

log = logging.getLogger(__name__)

# job name -> {"last_run", "ok", "message"}; in-memory, shown at /status
STATE: dict[str, dict] = {}
_alerted: set[str] = set()


async def _run(name: str, fn):
    try:
        result = await fn()
        STATE[name] = {"last_run": utcnow(), "ok": True, "message": str(result)}
        _alerted.discard(name)
    except Exception as e:
        STATE[name] = {"last_run": utcnow(), "ok": False, "message": type(e).__name__}
        log.warning("job %s failed: %s", name, type(e).__name__)
        if name not in _alerted:  # alert once per failure streak, never loop
            _alerted.add(name)
            await send_discord({"content": f"Manga tracker job `{name}` failed ({type(e).__name__}). It will keep retrying quietly."})


async def job_import():
    async def go():
        with SessionLocal() as db:
            return upsert_library(db, await fetch_library(get_settings().anilist_username))
    await _run("import", go)


async def job_push():
    async def go():
        with SessionLocal() as db:
            return await push_dirty(db)
    await _run("push", go)


async def job_chapters():
    async def go():
        with SessionLocal() as db:
            events = await detect_new_chapters(db, MangaDexSource())
            sent = await notify_new_chapters(db)
            return {"new": len(events), "notified": sent}
    await _run("chapters", go)
