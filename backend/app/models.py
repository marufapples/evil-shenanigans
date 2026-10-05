from datetime import datetime
from enum import Enum
from pydantic import BaseModel, HttpUrl

class PublishingStatus(str, Enum):
    FINISHED = "FINISHED"
    RELEASING = "RELEASING"
    NOT_YET_RELEASED = "NOT_YET_RELEASED"
    CANCELLED = "CANCELLED"
    HIATUS = "HIATUS"

class MangaEntry(BaseModel):
    anilist_id: int
    title: str
    progress: int
    status: PublishingStatus
    total_chapters: int | None
    cover: HttpUrl
    updated_at: datetime