from app.importer import upsert_library
from app.orm import Manga
from tests.conftest import row

MD = "0153e96a-fb57-4665-a988-754b4f3aa744"


def test_list_and_override_rebaselines(client, db):
    upsert_library(db, [row(1, "A"), row(2, "B", list_status="PLANNING")])
    m = db.query(Manga).filter_by(anilist_id=1).one()
    m.latest_known_chapter = 40
    db.commit()
    assert [x["title"] for x in client.get("/chapters/matches").json()] == ["A"]
    assert client.put(f"/chapters/matches/{m.id}", json={"mangadex_id": MD}).status_code == 200
    db.refresh(m)
    assert m.mangadex_id == MD and m.latest_known_chapter is None


def test_override_validation(client, db):
    upsert_library(db, [row()])
    m = db.query(Manga).one()
    assert client.put(f"/chapters/matches/{m.id}", json={"mangadex_id": "../evil"}).status_code == 422
    assert client.put("/chapters/matches/999", json={"mangadex_id": None}).status_code == 404
