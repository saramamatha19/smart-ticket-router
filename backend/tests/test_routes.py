"""
API-level test for the /route-ticket error path. test_router_service.py
already proves route_ticket() itself raises correctly on failure -- this
proves the *whole chain*, route handler included, turns that into a
clean 502 with no leaked exception detail (the actual Task 4 requirement).
"""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.auth.security import create_access_token
from app.database.connection import get_db
from main import app

_AUTH_HEADERS = {"Authorization": f"Bearer {create_access_token(subject='1', role='customer')}"}


def _override_get_db():
    yield MagicMock()


def test_route_ticket_endpoint_returns_502_without_leaking_exception():
    app.dependency_overrides[get_db] = _override_get_db

    try:
        with patch(
            "app.router.routes.route_ticket",
            side_effect=RuntimeError("some internal detail that must not leak"),
        ):
            client = TestClient(app)
            response = client.post(
                "/route-ticket", json={"message": "test ticket"}, headers=_AUTH_HEADERS
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 502
    body = response.json()
    assert "some internal detail" not in body["detail"]


def test_route_ticket_endpoint_returns_422_for_blank_message():
    """A whitespace-only message must fail Pydantic validation before
    ever reaching route_ticket(), returning FastAPI's normal 422 --
    not a 502 from a wasted OpenAI call."""
    client = TestClient(app)
    response = client.post("/route-ticket", json={"message": "   "}, headers=_AUTH_HEADERS)

    assert response.status_code == 422
