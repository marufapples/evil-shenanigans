from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app import jobs


def build_scheduler() -> AsyncIOScheduler:
    sched = AsyncIOScheduler()
    sched.add_job(jobs.job_import, "interval", minutes=30, jitter=120, id="import", max_instances=1, coalesce=True)
    sched.add_job(jobs.job_push, "interval", minutes=10, jitter=30, id="push", max_instances=1, coalesce=True)
    sched.add_job(jobs.job_chapters, "interval", minutes=30, jitter=180, id="chapters", max_instances=1, coalesce=True)
    return sched
