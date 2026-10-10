from app.config import Settings


def test_defaults_do_not_require_env(monkeypatch):
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    s = Settings(_env_file=None)
    assert s.discord_webhook_url == ""
    assert s.database_url.startswith("sqlite:///")
