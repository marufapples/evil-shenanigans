import httpx
from app.models import MangaEntry

ANILIST_URL = "https://graphql.anilist.co"
READING_QUERY = """query ($user: String) { MediaListCollection(userName: $user, type: MANGA, status: CURRENT) {
  lists { entries { progress updatedAt media { id title { romaji english } chapters status coverImage { large } } } } } }"""

async def fetch_reading_list(username: str) -> list[MangaEntry]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(ANILIST_URL, json={"query": READING_QUERY, "variables": {"user": username}})
    body = resp.json()
    if body.get("errors"):
        raise ValueError(body["errors"][0]["message"])
    resp.raise_for_status()
    entries = [e for lst in body["data"]["MediaListCollection"]["lists"] for e in lst["entries"]]
    return [{
        "anilist_id": e["media"]["id"],
        "title": e["media"]["title"]["english"] or e["media"]["title"]["romaji"],
        "progress": e["progress"],
        "status": e["media"]["status"],
        "total_chapters": e["media"]["chapters"],
        "cover": e["media"]["coverImage"]["large"],
        "updated_at": e["updatedAt"],
    } for e in entries]