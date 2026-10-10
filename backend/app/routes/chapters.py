from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.detect import TRACKED_STATUSES, detect_new_chapters
from app.orm import ChapterEvent, LibraryEntry, Manga
from app.sources.mangadex import MangaDexSource

router = APIRouter(prefix="/chapters")


@router.post("/check")
async def check(db: Session = Depends(get_db)):
    events = await detect_new_chapters(db, MangaDexSource())
    return {"new": [{"manga": e.manga.title, "chapter": e.chapter} for e in events]}


@router.get("/events")
def events(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.scalars(select(ChapterEvent).options(joinedload(ChapterEvent.manga))
                      .order_by(ChapterEvent.detected_at.desc()).limit(limit))
    return [{"id": e.id, "manga": e.manga.title, "chapter": e.chapter, "url": e.url,
             "detected_at": e.detected_at, "notified": e.notified} for e in rows]


class MatchIn(BaseModel):
    mangadex_id: str | None = Field(None, pattern=r"^[0-9a-f-]{36}$")


@router.get("/matches")
def matches(db: Session = Depends(get_db)):
    stmt = (select(Manga).join(LibraryEntry).where(LibraryEntry.list_status.in_(TRACKED_STATUSES))
            .order_by(Manga.title))
    return [{"id": m.id, "title": m.title, "publishing_status": m.publishing_status, "mangadex_id": m.mangadex_id,
             "latest_known_chapter": m.latest_known_chapter} for m in db.scalars(stmt)]


@router.put("/matches/{manga_id}")
def set_match(manga_id: int, body: MatchIn, db: Session = Depends(get_db)):
    manga = db.get(Manga, manga_id)
    if not manga:
        raise HTTPException(404, "manga not found")
    manga.mangadex_id = body.mangadex_id
    manga.latest_known_chapter = None  # re-baseline so a manual change never fires a false alert
    manga.source_checked_at = datetime.utcnow()
    db.commit()
    return {"id": manga.id, "mangadex_id": manga.mangadex_id}
