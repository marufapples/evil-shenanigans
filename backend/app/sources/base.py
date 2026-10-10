from typing import Protocol


class ChapterSource(Protocol):
    name: str

    async def find_series(self, anilist_id: int, titles: list[str]) -> str | None:
        """Return the source's id for this series, or None if no confident match."""

    async def latest_chapter(self, series_id: str) -> float | None:
        """Highest known chapter number, or None if the source has no chapters."""

    def chapter_url(self, series_id: str) -> str: ...
