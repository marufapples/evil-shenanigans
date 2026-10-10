from datetime import datetime

import httpx
import respx

from app import jobs
from app.importer import upsert_library
from app.notify import notify_new_chapters
from app.orm import ChapterEvent, Manga
from tests.conftest import row

HOOK = "https://discord.test/api/webhooks/1/abc"


def _events(db, n):
    upsert_library(db, [row()])
    m = db.query(Manga).one()
    for i in range(n):
        db.add(ChapterEvent(manga=m, chapter=i + 1, source="fake", url="http://x", detected_at=datetime(2026, 1, 1, 0, i)))
    db.commit()


@respx.mock
async def test_batches_of_ten_and_marks_notified(db, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", HOOK)
    from app.config import get_settings
    get_settings.cache_clear()
    route = respx.post(HOOK).mock(return_value=httpx.Response(204))
    _events(db, 12)
    assert await notify_new_chapters(db) == 12
    assert route.call_count == 2
    assert db.query(ChapterEvent).filter_by(notified=False).count() == 0
    get_settings.cache_clear()


@respx.mock
async def test_failure_leaves_events_unsent(db, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", HOOK)
    from app.config import get_settings
    get_settings.cache_clear()
    respx.post(HOOK).mock(return_value=httpx.Response(500))
    _events(db, 2)
    assert await notify_new_chapters(db) == 0
    assert db.query(ChapterEvent).filter_by(notified=False).count() == 2
    get_settings.cache_clear()


@respx.mock
async def test_job_failure_alerts_once(monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", HOOK)
    from app.config import get_settings
    get_settings.cache_clear()
    route = respx.post(HOOK).mock(return_value=httpx.Response(204))
    jobs._alerted.clear()

    async def boom():
        raise RuntimeError("secret detail")

    await jobs._run("t", boom)
    await jobs._run("t", boom)
    assert route.call_count == 1
    assert jobs.STATE["t"]["message"] == "RuntimeError"  # no exception text stored
    get_settings.cache_clear()
