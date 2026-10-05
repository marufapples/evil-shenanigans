from fastapi import FastAPI, HTTPException
from app.anilist import fetch_reading_list
from app.models import MangaEntry

app = FastAPI(title="Manga Tracker")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/users/{username}/reading", response_model=list[MangaEntry])
async def get_reading(username: str):
    try:
        return await fetch_reading_list(username)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))