from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import run_migrations
from app.routes import auth, chapters, library


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield


app = FastAPI(title="Manga Tracker", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_url],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(library.router)
app.include_router(auth.router)
app.include_router(chapters.router)


@app.get("/health")
def health():
    return {"status": "ok"}
