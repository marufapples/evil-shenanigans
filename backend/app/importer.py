from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.orm import LibraryEntry, Manga

MANGA_FIELDS = ["title", "alt_titles", "cover", "publishing_status", "total_chapters", "country", "format"]
ENTRY_FIELDS = ["list_status", "progress", "score", "notes", "anilist_updated_at"]


def upsert_library(db: Session, rows: list[dict]) -> dict[str, int]:
    """Merge AniList rows into the DB. Entries with unpushed local edits (dirty) are left alone."""
    existing = {m.anilist_id: m for m in db.scalars(select(Manga))}
    stats = {"added": 0, "updated": 0, "skipped_dirty": 0}
    for row in rows:
        manga = existing.get(row["anilist_id"])
        if manga is None:
            manga = Manga(anilist_id=row["anilist_id"], **{k: row[k] for k in MANGA_FIELDS})
            manga.entry = LibraryEntry(**{k: row[k] for k in ENTRY_FIELDS})
            db.add(manga)
            stats["added"] += 1
            continue
        for k in MANGA_FIELDS:
            setattr(manga, k, row[k])
        if manga.entry is None:
            manga.entry = LibraryEntry(**{k: row[k] for k in ENTRY_FIELDS})
            stats["added"] += 1
        elif manga.entry.dirty:
            stats["skipped_dirty"] += 1
        else:
            for k in ENTRY_FIELDS:
                setattr(manga.entry, k, row[k])
            stats["updated"] += 1
    db.commit()
    return stats
