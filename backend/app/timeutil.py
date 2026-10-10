from datetime import UTC, datetime


def utcnow() -> datetime:
    """Naive UTC now; the DB stores naive UTC timestamps."""
    return datetime.now(UTC).replace(tzinfo=None)
