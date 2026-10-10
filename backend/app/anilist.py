import asyncio
from datetime import UTC, datetime

import httpx

ANILIST_URL = "https://graphql.anilist.co"

LIBRARY_QUERY = """
query ($user: String, $chunk: Int) {
  MediaListCollection(userName: $user, type: MANGA, chunk: $chunk, perChunk: 500) {
    hasNextChunk
    lists { entries {
      status progress score(format: POINT_10_DECIMAL) notes updatedAt
      media { id title { romaji english } synonyms chapters status format countryOfOrigin coverImage { large } }
    } }
  }
}"""


class AniListError(Exception):
    pass


def _parse_entry(e: dict) -> dict:
    m = e["media"]
    title = m["title"]["english"] or m["title"]["romaji"]
    alts = {t for t in [m["title"]["romaji"], m["title"]["english"], *(m.get("synonyms") or [])] if t and t != title}
    return {
        "anilist_id": m["id"],
        "title": title,
        "alt_titles": sorted(alts),
        "cover": (m.get("coverImage") or {}).get("large"),
        "publishing_status": m["status"],
        "total_chapters": m["chapters"],
        "country": m.get("countryOfOrigin"),
        "format": m.get("format"),
        "list_status": e["status"],
        "progress": e["progress"] or 0,
        "score": e["score"] or None,
        "notes": e.get("notes"),
        "anilist_updated_at": datetime.fromtimestamp(e["updatedAt"], UTC).replace(tzinfo=None),
    }


async def _post(client: httpx.AsyncClient, payload: dict, headers: dict | None = None) -> dict:
    for attempt in range(3):
        resp = await client.post(ANILIST_URL, json=payload, headers=headers or {})
        if resp.status_code == 429:
            await asyncio.sleep(min(int(resp.headers.get("Retry-After", "10")), 60))
            continue
        body = resp.json()
        if body.get("errors"):
            raise AniListError(body["errors"][0]["message"])
        resp.raise_for_status()
        return body["data"]
    raise AniListError("rate limited by AniList")


async def fetch_library(username: str) -> list[dict]:
    """Every manga list entry for a user, deduplicated by media id."""
    found: dict[int, dict] = {}
    async with httpx.AsyncClient(timeout=20) as client:
        chunk = 1
        while True:
            data = await _post(client, {"query": LIBRARY_QUERY, "variables": {"user": username, "chunk": chunk}})
            coll = data["MediaListCollection"]
            for lst in coll["lists"]:
                for e in lst["entries"]:
                    found[e["media"]["id"]] = _parse_entry(e)
            if not coll["hasNextChunk"]:
                return list(found.values())
            chunk += 1


OAUTH_AUTHORIZE = "https://anilist.co/api/v2/oauth/authorize"
OAUTH_TOKEN = "https://anilist.co/api/v2/oauth/token"

VIEWER_QUERY = "query { Viewer { id name } }"
SAVE_MUTATION = """
mutation ($mediaId: Int, $status: MediaListStatus, $progress: Int, $score: Int, $notes: String) {
  SaveMediaListEntry(mediaId: $mediaId, status: $status, progress: $progress, scoreRaw: $score, notes: $notes) { id progress status }
}"""


def authorize_url(client_id: str, redirect_uri: str) -> str:
    from urllib.parse import urlencode

    return f"{OAUTH_AUTHORIZE}?{urlencode({'client_id': client_id, 'redirect_uri': redirect_uri, 'response_type': 'code'})}"


async def exchange_code(client_id: str, client_secret: str, redirect_uri: str, code: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(OAUTH_TOKEN, json={
            "grant_type": "authorization_code", "client_id": client_id, "client_secret": client_secret,
            "redirect_uri": redirect_uri, "code": code,
        })
    if resp.status_code != 200:
        raise AniListError("AniList rejected the authorization code")  # never include the response body
    return resp.json()


async def fetch_viewer(token: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        data = await _post(client, {"query": VIEWER_QUERY}, {"Authorization": f"Bearer {token}"})
    return data["Viewer"]


async def save_entry(token: str, media_id: int, status: str, progress: int, score: float | None, notes: str | None) -> None:
    variables = {"mediaId": media_id, "status": status, "progress": progress,
                 "score": round((score or 0) * 10), "notes": notes}
    async with httpx.AsyncClient(timeout=20) as client:
        await _post(client, {"query": SAVE_MUTATION, "variables": variables}, {"Authorization": f"Bearer {token}"})
