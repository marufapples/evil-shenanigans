import httpx
import respx

from app.anilist import ANILIST_URL, OAUTH_TOKEN
from app.importer import upsert_library
from app.orm import LibraryEntry, OAuthToken
from tests.conftest import row


def _connect(db):
    db.add(OAuthToken(provider="anilist", access_token="tok", account_name="me"))
    db.commit()


def test_login_requires_config(client, monkeypatch):
    monkeypatch.setenv("ANILIST_CLIENT_ID", "")
    from app.config import get_settings
    get_settings.cache_clear()
    assert client.get("/auth/anilist/login", follow_redirects=False).status_code in (302, 307, 400)
    get_settings.cache_clear()


@respx.mock
def test_callback_stores_token_without_leaking(client, db):
    respx.post(OAUTH_TOKEN).mock(return_value=httpx.Response(200, json={"access_token": "secret-abc", "expires_in": 3600}))
    respx.post(ANILIST_URL).mock(return_value=httpx.Response(200, json={"data": {"Viewer": {"id": 1, "name": "me"}}}))
    r = client.get("/auth/anilist/callback?code=xyz", follow_redirects=False)
    assert r.status_code == 307 and "connected=1" in r.headers["location"]
    status = client.get("/auth/anilist/status")
    assert status.json() == {"connected": True, "account": "me"}
    assert "secret-abc" not in status.text


@respx.mock
def test_patch_marks_dirty_and_pushes_when_connected(client, db):
    upsert_library(db, [row()])
    _connect(db)
    route = respx.post(ANILIST_URL).mock(return_value=httpx.Response(200, json={"data": {"SaveMediaListEntry": {"id": 1}}}))
    entry = db.query(LibraryEntry).one()
    r = client.patch(f"/library/{entry.id}", json={"progress": 12})
    assert r.status_code == 200 and r.json()["progress"] == 12 and r.json()["dirty"] is False
    assert route.call_count == 1


def test_patch_stays_dirty_when_not_connected_then_push_noop(client, db):
    upsert_library(db, [row()])
    entry = db.query(LibraryEntry).one()
    assert client.patch(f"/library/{entry.id}", json={"progress": 7}).json()["dirty"] is True
    assert client.post("/library/push").json() == {"pushed": 0, "pending": 1}


@respx.mock
def test_failed_push_stays_dirty(client, db):
    upsert_library(db, [row()])
    _connect(db)
    respx.post(ANILIST_URL).mock(return_value=httpx.Response(500, json={}))
    entry = db.query(LibraryEntry).one()
    assert client.patch(f"/library/{entry.id}", json={"progress": 8}).json()["dirty"] is True


def test_patch_validation(client, db):
    upsert_library(db, [row()])
    entry = db.query(LibraryEntry).one()
    assert client.patch(f"/library/{entry.id}", json={"score": 99}).status_code == 422
