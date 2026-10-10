import logging

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.orm import ChapterEvent

log = logging.getLogger(__name__)
MAX_EMBEDS = 10


def _fmt(n: float) -> str:
    return str(int(n)) if n == int(n) else str(n)


async def send_discord(payload: dict, url: str | None = None) -> bool:
    url = url or get_settings().discord_webhook_url
    if not url:
        return False
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload)
        if resp.status_code == 429:
            return False  # try again next tick
        return resp.status_code in (200, 204)
    except httpx.HTTPError as e:
        log.warning("Discord send failed: %s", type(e).__name__)  # never log the webhook URL
        return False


async def notify_new_chapters(db: Session) -> int:
    """Send every unnotified chapter event, 10 per message. Events are marked sent only on success."""
    events = db.scalars(select(ChapterEvent).options(joinedload(ChapterEvent.manga))
                        .where(ChapterEvent.notified.is_(False)).order_by(ChapterEvent.detected_at)).all()
    sent = 0
    for i in range(0, len(events), MAX_EMBEDS):
        batch = events[i : i + MAX_EMBEDS]
        embeds = [{
            "title": f"{e.manga.title}: chapter {_fmt(e.chapter)}",
            "url": e.url,
            "thumbnail": {"url": e.manga.cover} if e.manga.cover else None,
            "footer": {"text": f"via {e.source}"},
        } for e in batch]
        embeds = [{k: v for k, v in em.items() if v} for em in embeds]
        if not await send_discord({"content": "New chapters", "embeds": embeds}):
            break
        for e in batch:
            e.notified = True
        db.commit()
        sent += len(batch)
    return sent
