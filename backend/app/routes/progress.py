from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import progress as pg
from app.db import get_db
from app.sync import push_entry

router = APIRouter(prefix="/progress")


class Report(BaseModel):
    url: str
    title: str = ""
    chapter: float | None = None
    anilist_id: int | None = None


async def _handle(db: Session, token: str, r: Report) -> dict:
    if token != pg.get_progress_token(db):
        raise HTTPException(403, "bad token")
    chapter = r.chapter if r.chapter is not None else pg.parse_chapter(r.url, r.title)
    if chapter is None:
        return {"status": "no_chapter"}
    manga, candidates = pg.resolve_manga(db, r.url, r.title, r.anilist_id)
    if manga is None:
        return {"status": "ambiguous", "chapter": chapter,
                "candidates": [{"anilist_id": c.anilist_id, "title": c.title} for c in candidates]}
    pg.link_site(db, manga, r.url)
    entry = pg.apply_progress(db, manga, chapter)
    if entry is None:
        return {"status": "unchanged", "manga": manga.title}
    await push_entry(db, entry)
    return {"status": "updated", "manga": manga.title, "progress": entry.progress}


@router.post("")
async def report(r: Report, token: str = Query(...), db: Session = Depends(get_db)):
    return await _handle(db, token, r)


@router.get("/report")
async def report_get(url: str, token: str, title: str = "", anilist_id: int | None = None, db: Session = Depends(get_db)):
    """GET variant for bookmarklets (image beacon)."""
    return await _handle(db, token, Report(url=url, title=title, anilist_id=anilist_id))


@router.get("/userscript", response_class=PlainTextResponse)
def userscript(db: Session = Depends(get_db)):
    token = pg.get_progress_token(db)
    return f"""// ==UserScript==
// @name         Manga Tracker progress
// @match        *://*/*
// @grant        GM_xmlhttpRequest
// @connect      localhost
// ==/UserScript==
(function () {{
  const m = /(chapter|chap|ch|episode|ep)[\\s._/-]*\\d+/i;
  if (!m.test(location.pathname) && !m.test(document.title)) return;
  GM_xmlhttpRequest({{
    method: "POST",
    url: "http://localhost:8000/progress?token={token}",
    headers: {{ "Content-Type": "application/json" }},
    data: JSON.stringify({{ url: location.href, title: document.title }}),
  }});
}})();
"""
