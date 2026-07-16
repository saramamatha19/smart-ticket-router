"""Tests for /admin/login and the JWT guard placed on the admin-facing
/tickets and /tickets/stats endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.auth.security import ADMIN_PASSWORD, ADMIN_USERNAME, create_access_token
from app.database.connection import get_db
from main import app

client = TestClient(app)


def _override_get_db():
    yield MagicMock()


def test_login_succeeds_with_correct_credentials():
    response = client.post("/admin/login", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_fails_with_wrong_password():
    response = client.post("/admin/login", json={"username": ADMIN_USERNAME, "password": "wrong-password"})

    assert response.status_code == 401


def test_tickets_endpoint_rejects_missing_token():
    response = client.get("/tickets")

    assert response.status_code == 401


def test_tickets_endpoint_rejects_garbage_token():
    response = client.get("/tickets", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_tickets_stats_endpoint_rejects_missing_token():
    response = client.get("/tickets/stats")

    assert response.status_code == 401


def test_tickets_endpoint_rejects_a_customer_token():
    """A customer's JWT has role="customer" -- it must not work here,
    even though it's signed with the same secret as an admin token."""
    customer_token = create_access_token(subject="1", role="customer")

    response = client.get("/tickets", headers={"Authorization": f"Bearer {customer_token}"})

    assert response.status_code == 401


def test_tickets_endpoint_accepts_valid_token():
    app.dependency_overrides[get_db] = _override_get_db

    try:
        login_response = client.post(
            "/admin/login", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )
        token = login_response.json()["access_token"]

        with (
            patch("app.router.routes.get_all_tickets", return_value=[]),
            patch("app.router.routes.get_ticket_count", return_value=0),
        ):
            response = client.get("/tickets", headers={"Authorization": f"Bearer {token}"})
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json() == []
