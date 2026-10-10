"""Pydantic schemas (API and AniList payload shapes)."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class PublishingStatus(str, Enum):
    FINISHED = "FINISHED"
    RELEASING = "RELEASING"
    NOT_YET_RELEASED = "NOT_YET_RELEASED"
    CANCELLED = "CANCELLED"
    HIATUS = "HIATUS"


class ListStatus(str, Enum):
    CURRENT = "CURRENT"
    PLANNING = "PLANNING"
    COMPLETED = "COMPLETED"
    DROPPED = "DROPPED"
    PAUSED = "PAUSED"
    REPEATING = "REPEATING"


class MangaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    anilist_id: int
    title: str
    alt_titles: list[str]
    cover: str | None
    publishing_status: PublishingStatus
    total_chapters: int | None
    country: str | None
    format: str | None
    latest_known_chapter: float | None


class LibraryEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    list_status: ListStatus
    progress: int
    score: float | None
    notes: str | None
    anilist_updated_at: datetime | None
    local_updated_at: datetime | None
    dirty: bool
    manga: MangaOut
