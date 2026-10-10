import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.anilist import AniListError, save_entry
from app.orm import LibraryEntry, OAuthToken

log = logging.getLogger(__name__)


def get_token(db: Session) -> OAuthToken | None:
    tok = db.scalar(select(OAuthToken).where(OAuthToken.provider == "anilist"))
    if tok and tok.expires_at and tok.expires_at < datetime.utcnow():
        return None
    return tok


async def push_entry(db: Session, entry: LibraryEntry) -> bool:
    """Push one entry to AniList. Returns True on success; failures leave it dirty for the next sync."""
    tok = get_token(db)
    if not tok:
        return False
    try:
        await save_entry(tok.access_token, entry.manga.anilist_id, entry.list_status, entry.progress, entry.score, entry.notes)
    except Exception as e:  # network/auth: keep dirty, retry later, never loop
        log.warning("AniList push failed for %s: %s", entry.manga.anilist_id, type(e).__name__)
        return False
    entry.dirty = False
    db.commit()
    return True


async def push_dirty(db: Session) -> dict[str, int]:
    entries = db.scalars(select(LibraryEntry).where(LibraryEntry.dirty.is_(True))).all()
    ok = 0
    for entry in entries:
        if await push_entry(db, entry):
            ok += 1
        elif get_token(db) is None:
            break
    return {"pushed": ok, "pending": len(entries) - ok}
