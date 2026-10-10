from app.importer import upsert_library
from app.orm import LibraryEntry, ReadingSiteLink
from app.progress import get_progress_token, parse_chapter, site_key
from tests.conftest import row


def test_parse_chapter():
    assert parse_chapter("https://s.com/manga/dungeon-odyssey/chapter-128") == 128
    assert parse_chapter("https://s.com/x", "Dungeon Odyssey Chapter 12.5 - Site") == 12.5
    assert parse_chapter("https://s.com/x", "Home") is None


def test_site_key():
    assert site_key("https://S.com/manga/slug/chapter-9") == ("s.com", "/manga/slug")


def test_report_updates_forward_only_and_links(client, db):
    upsert_library(db, [row(1, "Dungeon Odyssey", progress=100)])
    t = get_progress_token(db)
    body = {"url": "https://s.com/manga/do/chapter-128", "title": "Dungeon Odyssey Chapter 128"}
    r = client.post(f"/progress?token={t}", json=body).json()
    assert r["status"] == "updated" and r["progress"] == 128
    assert db.query(ReadingSiteLink).count() == 1
    assert client.post(f"/progress?token={t}", json=body).json()["status"] == "unchanged"
    # later report resolves via link even with an unhelpful title
    r = client.post(f"/progress?token={t}", json={"url": "https://s.com/manga/do/chapter-129", "title": "Reader"}).json()
    assert r["status"] == "updated" and db.query(LibraryEntry).one().progress == 129


def test_bad_token_and_ambiguous(client, db):
    upsert_library(db, [row(1, "Alpha Tale"), row(2, "Beta Story")])
    assert client.post("/progress?token=nope", json={"url": "https://s.com/chapter-1"}).status_code == 403
    t = get_progress_token(db)
    r = client.post(f"/progress?token={t}", json={"url": "https://s.com/q/chapter-3", "title": "Gamma Chapter 3"}).json()
    assert r["status"] == "ambiguous" and r["candidates"]


def test_userscript_embeds_token(client, db):
    t = get_progress_token(db)
    assert t in client.get("/progress/userscript").text
