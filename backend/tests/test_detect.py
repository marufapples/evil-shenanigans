from datetime import datetime

import httpx
import respx

from app.detect import detect_new_chapters
from app.importer import upsert_library
from app.orm import ChapterEvent, Manga
from app.sources.mangadex import API, MangaDexSource
from tests.conftest import row


class FakeSource:
    name = "fake"

    def __init__(self, latest):
        self.latest, self.found = latest, "sid"

    async def find_series(self, anilist_id, titles):
        return self.found

    async def latest_chapter(self, series_id):
        return self.latest

    def chapter_url(self, series_id):
        return f"http://x/{series_id}"


async def test_baseline_then_new_chapter(db):
    upsert_library(db, [row()])
    assert await detect_new_chapters(db, FakeSource(10)) == []  # baseline, no alert
    assert db.query(Manga).one().latest_known_chapter == 10
    assert await detect_new_chapters(db, FakeSource(10)) == []
    events = await detect_new_chapters(db, FakeSource(11))
    assert [e.chapter for e in events] == [11] and db.query(ChapterEvent).count() == 1


async def test_ignores_finished_and_planning(db):
    upsert_library(db, [row(1, publishing_status="FINISHED"), row(2, list_status="PLANNING")])
    await detect_new_chapters(db, FakeSource(5))
    assert db.query(Manga).filter(Manga.latest_known_chapter.isnot(None)).count() == 0


async def test_unmatched_not_rechecked_for_a_week(db):
    upsert_library(db, [row()])
    src = FakeSource(3)
    src.found = None
    now = datetime(2026, 1, 1)
    await detect_new_chapters(db, src, now)
    src.found = "sid"
    await detect_new_chapters(db, src, datetime(2026, 1, 3))
    assert db.query(Manga).one().mangadex_id is None
    await detect_new_chapters(db, src, datetime(2026, 1, 9))
    assert db.query(Manga).one().mangadex_id == "sid"


@respx.mock
async def test_mangadex_exact_link_and_latest():
    respx.get(f"{API}/manga").mock(return_value=httpx.Response(200, json={"data": [
        {"id": "wrong", "attributes": {"title": {"en": "Other"}, "altTitles": [], "links": {"al": "9"}}},
        {"id": "right", "attributes": {"title": {"en": "Berserk"}, "altTitles": [], "links": {"al": "30002"}}}]}))
    respx.get(f"{API}/manga/right/aggregate").mock(return_value=httpx.Response(200, json={
        "volumes": {"1": {"chapters": {"1": {}, "2": {}, "2.5": {}}}, "none": {"chapters": {"10": {}}}}}))
    src = MangaDexSource(delay=0)
    assert await src.find_series(30002, ["Berserk"]) == "right"
    assert await src.latest_chapter("right") == 10


@respx.mock
async def test_mangadex_empty_volumes_list():
    respx.get(f"{API}/manga/x/aggregate").mock(return_value=httpx.Response(200, json={"volumes": []}))
    assert await MangaDexSource(delay=0).latest_chapter("x") is None
