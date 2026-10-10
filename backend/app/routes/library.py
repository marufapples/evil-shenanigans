
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.anilist import AniListError, fetch_library
from app.config import get_settings
from app.db import get_db
from app.importer import upsert_library
from app.models import LibraryEntryOut, ListStatus
from app.orm import LibraryEntry, Manga
from app.sync import push_dirty, push_entry
from app.timeutil import utcnow

router = APIRouter()

SORTS = {
    "title": Manga.title,
    "progress": LibraryEntry.progress,
    "score": LibraryEntry.score.desc(),
    "updated": LibraryEntry.anilist_updated_at.desc(),
}


@router.get("/library", response_model=list[LibraryEntryOut])
def list_library(
    status: ListStatus | None = None,
    q: str | None = Query(None, description="title substring"),
    sort: str = Query("updated", pattern="^(title|progress|score|updated)$"),
    db: Session = Depends(get_db),
):
    stmt = select(LibraryEntry).join(Manga).options(joinedload(LibraryEntry.manga))
    if status:
        stmt = stmt.where(LibraryEntry.list_status == status.value)
    if q:
        stmt = stmt.where(Manga.title.ilike(f"%{q}%"))
    return db.scalars(stmt.order_by(SORTS[sort])).all()


@router.get("/library/{entry_id}", response_model=LibraryEntryOut)
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(LibraryEntry, entry_id)
    if not entry:
        raise HTTPException(404, "entry not found")
    return entry


@router.post("/library/import")
async def import_from_anilist(db: Session = Depends(get_db)):
    username = get_settings().anilist_username
    if not username:
        raise HTTPException(400, "ANILIST_USERNAME is not set")
    try:
        rows = await fetch_library(username)
    except AniListError as e:
        raise HTTPException(502, str(e))
    return upsert_library(db, rows)


class EntryPatch(BaseModel):
    list_status: ListStatus | None = None
    progress: int | None = Field(None, ge=0)
    score: float | None = Field(None, ge=0, le=10)
    notes: str | None = None


@router.patch("/library/{entry_id}", response_model=LibraryEntryOut)
async def update_entry(entry_id: int, patch: EntryPatch, db: Session = Depends(get_db)):
    entry = db.get(LibraryEntry, entry_id)
    if not entry:
        raise HTTPException(404, "entry not found")
    for k, v in patch.model_dump(exclude_unset=True).items():
        setattr(entry, k, v.value if isinstance(v, ListStatus) else v)
    entry.local_updated_at = utcnow()
    entry.dirty = True
    db.commit()
    await push_entry(db, entry)  # best effort; stays dirty if not connected/offline
    return entry


@router.post("/library/push")
async def push_pending(db: Session = Depends(get_db)):
    return await push_dirty(db)
