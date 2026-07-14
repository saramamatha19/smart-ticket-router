"""
Lightweight read-only integration test against the real dev database —
verifies GET /tickets pagination behaves correctly against actual rows,
not a mocked query chain. Skips (not fails) if no DB is reachable.
"""

import pytest

from app.crud.ticket_crud import get_all_tickets
from app.database.connection import SessionLocal


@pytest.fixture
def db_session():
    try:
        session = SessionLocal()
        session.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:
        pytest.skip("No database available in this environment")

    yield session
    session.close()


def test_get_all_tickets_respects_limit(db_session):
    unlimited = get_all_tickets(db_session)
    limited = get_all_tickets(db_session, limit=2)

    assert len(limited) <= 2
    assert len(limited) <= len(unlimited)

    if len(unlimited) >= 2:
        # newest-first ordering must be preserved under a limit
        assert [t.id for t in limited] == [t.id for t in unlimited[:2]]
