from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Manga(Base):
    __tablename__ = "manga"

    id: Mapped[int] = mapped_column(primary_key=True)
    anilist_id: Mapped[int] = mapped_column(unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    alt_titles: Mapped[list[str]] = mapped_column(JSON, default=list)
    cover: Mapped[str | None] = mapped_column(String(1000))
    publishing_status: Mapped[str] = mapped_column(String(32))
    total_chapters: Mapped[int | None]
    country: Mapped[str | None] = mapped_column(String(8))
    format: Mapped[str | None] = mapped_column(String(32))
    mangadex_id: Mapped[str | None] = mapped_column(String(64))
    source_checked_at: Mapped[datetime | None]
    latest_known_chapter: Mapped[float | None]

    entry: Mapped["LibraryEntry | None"] = relationship(back_populates="manga", uselist=False, cascade="all, delete-orphan")


class LibraryEntry(Base):
    __tablename__ = "library_entry"

    id: Mapped[int] = mapped_column(primary_key=True)
    manga_id: Mapped[int] = mapped_column(ForeignKey("manga.id"), unique=True)
    list_status: Mapped[str] = mapped_column(String(16), index=True)
    progress: Mapped[int] = mapped_column(default=0)
    score: Mapped[float | None]
    notes: Mapped[str | None]
    anilist_updated_at: Mapped[datetime | None]
    local_updated_at: Mapped[datetime | None]
    dirty: Mapped[bool] = mapped_column(default=False)

    manga: Mapped[Manga] = relationship(back_populates="entry")


class OAuthToken(Base):
    __tablename__ = "oauth_token"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), unique=True)
    access_token: Mapped[str] = mapped_column(String(4000))
    expires_at: Mapped[datetime | None]
    account_name: Mapped[str | None] = mapped_column(String(200))


class ChapterEvent(Base):
    __tablename__ = "chapter_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    manga_id: Mapped[int] = mapped_column(ForeignKey("manga.id"), index=True)
    chapter: Mapped[float]
    source: Mapped[str] = mapped_column(String(32))
    url: Mapped[str | None] = mapped_column(String(1000))
    detected_at: Mapped[datetime]
    notified: Mapped[bool] = mapped_column(default=False)

    manga: Mapped[Manga] = relationship()
