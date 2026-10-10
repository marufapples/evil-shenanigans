from app.importer import upsert_library
from app.orm import LibraryEntry
from tests.conftest import row


def test_adds_then_updates(db):
    assert upsert_library(db, [row()]) == {"added": 1, "updated": 0, "skipped_dirty": 0}
    assert upsert_library(db, [row(progress=9)])["updated"] == 1
    assert db.query(LibraryEntry).one().progress == 9


def test_dirty_entries_not_overwritten(db):
    upsert_library(db, [row()])
    entry = db.query(LibraryEntry).one()
    entry.progress, entry.dirty = 50, True
    db.commit()
    assert upsert_library(db, [row(progress=6)])["skipped_dirty"] == 1
    assert db.query(LibraryEntry).one().progress == 50
