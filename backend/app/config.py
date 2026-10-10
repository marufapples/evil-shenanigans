from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    anilist_client_id: str = ""
    anilist_client_secret: str = ""
    anilist_redirect_uri: str = "http://localhost:8000/auth/anilist/callback"
    anilist_username: str = ""
    discord_webhook_url: str = ""
    database_url: str = f"sqlite:///{BACKEND_DIR / 'data' / 'tracker.db'}"
    frontend_url: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
