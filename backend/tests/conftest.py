import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import orm  # noqa: F401
from app.db import Base, get_db
from app.main import app


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        yield session


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def row(anilist_id=1, title="Berserk", **over):
    base = {
        "anilist_id": anilist_id, "title": title, "alt_titles": [], "cover": "http://x/c.jpg",
        "publishing_status": "RELEASING", "total_chapters": None, "country": "JP", "format": "MANGA",
        "list_status": "CURRENT", "progress": 5, "score": 9.0, "notes": None, "anilist_updated_at": None,
    }
    return {**base, **over}
