from app.importer import upsert_library
from tests.conftest import row


def test_filter_search_sort(client, db):
    upsert_library(db, [row(1, "Berserk"), row(2, "Vagabond", list_status="PLANNING", progress=0), row(3, "Bleach", progress=1)])
    assert len(client.get("/library").json()) == 3
    assert [e["manga"]["title"] for e in client.get("/library?status=PLANNING").json()] == ["Vagabond"]
    assert [e["manga"]["title"] for e in client.get("/library?q=ber").json()] == ["Berserk"]
    assert [e["manga"]["title"] for e in client.get("/library?sort=title").json()] == ["Berserk", "Bleach", "Vagabond"]


def test_get_entry_404(client):
    assert client.get("/library/99").status_code == 404
