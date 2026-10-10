import asyncio

import httpx
from rapidfuzz import fuzz

API = "https://api.mangadex.org"
FUZZY_MIN = 95


def _num(raw: str) -> float | None:
    try:
        return float(raw)
    except ValueError:
        return None


class MangaDexSource:
    name = "mangadex"

    def __init__(self, client: httpx.AsyncClient | None = None, delay: float = 0.3):
        self._client = client
        self._delay = delay

    async def _get(self, path: str, params: dict) -> dict | None:
        client = self._client or httpx.AsyncClient(timeout=20, headers={"User-Agent": "manga-tracker/0.1"})
        try:
            await asyncio.sleep(self._delay)
            resp = await client.get(f"{API}{path}", params=params)
            if resp.status_code == 429:  # back off once, no loops
                await asyncio.sleep(min(int(resp.headers.get("Retry-After", "5")), 30))
                resp = await client.get(f"{API}{path}", params=params)
            if resp.status_code != 200:
                return None
            return resp.json()
        finally:
            if self._client is None:
                await client.aclose()

    async def find_series(self, anilist_id: int, titles: list[str]) -> str | None:
        best: tuple[int, str] | None = None
        for title in titles[:3]:
            body = await self._get("/manga", {"title": title, "limit": 10})
            for m in (body or {}).get("data", []):
                attrs = m["attributes"]
                if str((attrs.get("links") or {}).get("al")) == str(anilist_id):
                    return m["id"]
                names = [*attrs["title"].values(), *(v for alt in attrs.get("altTitles", []) for v in alt.values())]
                score = max((fuzz.ratio(title.lower(), n.lower()) for n in names), default=0)
                if score >= FUZZY_MIN and (best is None or score > best[0]):
                    best = (int(score), m["id"])
        return best[1] if best else None

    async def latest_chapter(self, series_id: str) -> float | None:
        body = await self._get(f"/manga/{series_id}/aggregate", {"translatedLanguage[]": "en"})
        volumes = (body or {}).get("volumes") or {}
        if isinstance(volumes, list):
            return None
        nums = [n for v in volumes.values() for c in v["chapters"] if (n := _num(c)) is not None]
        return max(nums) if nums else None

    def chapter_url(self, series_id: str) -> str:
        return f"https://mangadex.org/title/{series_id}"
