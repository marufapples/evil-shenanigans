from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app import jobs
from app.db import run_migrations
from app.notify import send_discord
from app.scheduler import build_scheduler
from app.routes import auth, chapters, library, progress


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    sched = None
    if get_settings().scheduler_enabled:
        sched = build_scheduler()
        sched.start()
    yield
    if sched:
        sched.shutdown(wait=False)


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
app.include_router(progress.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/status")
def status():
    return {k: {**v, "last_run": v["last_run"].isoformat()} for k, v in jobs.STATE.items()}


@app.post("/notify/test")
async def notify_test():
    ok = await send_discord({"content": "Manga tracker test notification"})
    return {"sent": ok}
