from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.anilist import AniListError, authorize_url, exchange_code, fetch_viewer
from app.config import get_settings
from app.db import get_db
from app.orm import OAuthToken
from app.sync import get_token
from app.timeutil import utcnow

router = APIRouter(prefix="/auth/anilist")


@router.get("/login")
def login():
    s = get_settings()
    if not (s.anilist_client_id and s.anilist_client_secret):
        raise HTTPException(400, "AniList client id/secret are not configured")
    return RedirectResponse(authorize_url(s.anilist_client_id, s.anilist_redirect_uri))


@router.get("/callback")
async def callback(code: str, db: Session = Depends(get_db)):
    s = get_settings()
    try:
        tok = await exchange_code(s.anilist_client_id, s.anilist_client_secret, s.anilist_redirect_uri, code)
        viewer = await fetch_viewer(tok["access_token"])
    except AniListError as e:
        raise HTTPException(502, str(e))
    row = db.query(OAuthToken).filter_by(provider="anilist").one_or_none() or OAuthToken(provider="anilist")
    row.access_token = tok["access_token"]
    row.expires_at = utcnow() + timedelta(seconds=tok.get("expires_in", 0)) if tok.get("expires_in") else None
    row.account_name = viewer["name"]
    db.add(row)
    db.commit()
    return RedirectResponse(f"{s.frontend_url}/settings?connected=1")


@router.get("/status")
def status(db: Session = Depends(get_db)):
    tok = get_token(db)
    return {"connected": tok is not None, "account": tok.account_name if tok else None}


@router.delete("/logout")
def logout(db: Session = Depends(get_db)):
    db.query(OAuthToken).filter_by(provider="anilist").delete()
    db.commit()
    return {"connected": False}
