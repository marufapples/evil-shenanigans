import httpx
import respx

from app.anilist import ANILIST_URL, fetch_library


def _entry(mid, status="CURRENT"):
    return {"status": status, "progress": 3, "score": 0, "notes": None, "updatedAt": 1700000000,
            "media": {"id": mid, "title": {"romaji": "R", "english": None}, "synonyms": ["S"], "chapters": None,
                      "status": "RELEASING", "format": "MANGA", "countryOfOrigin": "KR", "coverImage": {"large": "u"}}}


@respx.mock
async def test_paginates_and_dedupes():
    pages = [
        {"data": {"MediaListCollection": {"hasNextChunk": True, "lists": [{"entries": [_entry(1), _entry(2)]}]}}},
        {"data": {"MediaListCollection": {"hasNextChunk": False, "lists": [{"entries": [_entry(2), _entry(3)]}]}}},
    ]
    respx.post(ANILIST_URL).mock(side_effect=[httpx.Response(200, json=p) for p in pages])
    rows = await fetch_library("someone")
    assert sorted(r["anilist_id"] for r in rows) == [1, 2, 3]
    assert rows[0]["title"] == "R" and rows[0]["alt_titles"] == ["S"] and rows[0]["score"] is None
