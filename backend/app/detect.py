import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.orm import ChapterEvent, LibraryEntry, Manga
from app.sources.base import ChapterSource
from app.timeutil import utcnow

log = logging.getLogger(__name__)
RECHECK_MATCH_AFTER = timedelta(days=7)
TRACKED_STATUSES = ("CURRENT", "REPEATING")
ACTIVE_PUBLISHING = ("RELEASING", "HIATUS")


async def detect_new_chapters(db: Session, source: ChapterSource, now: datetime | None = None) -> list[ChapterEvent]:
    """Check every manga being read for chapters newer than the last known one.

    First sighting of a series only sets the baseline (no alert), so import never floods notifications.
    """
    now = now or utcnow()
    stmt = (
        select(Manga).join(LibraryEntry)
        .where(LibraryEntry.list_status.in_(TRACKED_STATUSES), Manga.publishing_status.in_(ACTIVE_PUBLISHING))
        .options(joinedload(Manga.entry))
    )
    events: list[ChapterEvent] = []
    for manga in db.scalars(stmt):
        if manga.mangadex_id is None:
            if manga.source_checked_at and now - manga.source_checked_at < RECHECK_MATCH_AFTER:
                continue
            manga.source_checked_at = now
            manga.mangadex_id = await source.find_series(manga.anilist_id, [manga.title, *manga.alt_titles])
            if manga.mangadex_id is None:
                continue
        latest = await source.latest_chapter(manga.mangadex_id)
        if latest is None:
            continue
        if manga.latest_known_chapter is not None and latest > manga.latest_known_chapter:
            ev = ChapterEvent(manga=manga, chapter=latest, source=source.name,
                              url=source.chapter_url(manga.mangadex_id), detected_at=now)
            db.add(ev)
            events.append(ev)
        if manga.latest_known_chapter is None or latest > manga.latest_known_chapter:
            manga.latest_known_chapter = latest
    db.commit()
    return events
