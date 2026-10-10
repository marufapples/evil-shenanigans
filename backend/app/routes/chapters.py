from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.detect import detect_new_chapters
from app.orm import ChapterEvent
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
