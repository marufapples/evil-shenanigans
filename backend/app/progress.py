import re
import secrets
from urllib.parse import urlparse

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.orm import LibraryEntry, Manga, OAuthToken, ReadingSiteLink
from app.timeutil import utcnow

CHAPTER_RE = re.compile(r"(?:chapter|chap|ch|episode|ep)[\s._/-]*(\d+(?:[._-]\d+)?)", re.I)
FUZZY_MIN = 90


def get_progress_token(db: Session) -> str:
    row = db.scalar(select(OAuthToken).where(OAuthToken.provider == "progress"))
    if not row:
        row = OAuthToken(provider="progress", access_token=secrets.token_urlsafe(24))
        db.add(row)
        db.commit()
    return row.access_token


def parse_chapter(url: str, title: str = "") -> float | None:
    for text in (urlparse(url).path, title):
        m = CHAPTER_RE.search(text)
        if m:
            return float(m.group(1).replace("_", ".").replace("-", "."))
    return None


def site_key(url: str) -> tuple[str, str]:
    u = urlparse(url)
    parts = []
    for seg in u.path.split("/"):
        if CHAPTER_RE.search(seg):
            break
        parts.append(seg)
    return u.netloc.lower(), "/".join(parts).rstrip("/")


def resolve_manga(db: Session, url: str, title: str, anilist_id: int | None = None) -> tuple[Manga | None, list[Manga]]:
    """Returns (match, candidates). match is set only when unambiguous."""
    if anilist_id is not None:
        return db.scalar(select(Manga).where(Manga.anilist_id == anilist_id)), []
    host, prefix = site_key(url)
    link = db.scalar(select(ReadingSiteLink).where(ReadingSiteLink.host == host, ReadingSiteLink.path_prefix == prefix))
    if link:
        return db.get(Manga, link.manga_id), []
    scored = []
    for m in db.scalars(select(Manga)):
        names = [m.title, *m.alt_titles]
        scored.append((max(fuzz.partial_ratio(n.lower(), title.lower()) for n in names) if title else 0, m))
    scored.sort(key=lambda t: -t[0])
    good = [m for s, m in scored if s >= FUZZY_MIN]
    if len(good) == 1:
        return good[0], []
    return None, good[:5] or [m for _, m in scored[:3]]


def link_site(db: Session, manga: Manga, url: str) -> None:
    host, prefix = site_key(url)
    if not db.scalar(select(ReadingSiteLink).where(ReadingSiteLink.host == host, ReadingSiteLink.path_prefix == prefix)):
        db.add(ReadingSiteLink(manga_id=manga.id, host=host, path_prefix=prefix))
        db.commit()


def apply_progress(db: Session, manga: Manga, chapter: float) -> LibraryEntry | None:
    """Moves progress forward only; returns the entry if it changed."""
    entry = manga.entry
    if entry is None:
        return None
    n = int(chapter)
    if n <= entry.progress:
        return None
    entry.progress = n
    if entry.list_status in ("PLANNING", "PAUSED", "DROPPED"):
        entry.list_status = "CURRENT"
    entry.local_updated_at = utcnow()
    entry.dirty = True
    db.commit()
    return entry
