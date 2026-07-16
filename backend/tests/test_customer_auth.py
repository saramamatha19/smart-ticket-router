"""Tests for customer /register and /login, and the JWT guard placed on
the customer-facing /route-ticket and /tickets/mine endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.auth.security import create_access_token, hash_password
from app.database.connection import get_db
from main import app

client = TestClient(app)


def _override_get_db():
    yield MagicMock()


def _fake_customer(customer_id=1, email="alice@example.com", password="hunter22"):
    customer = MagicMock()
    customer.id = customer_id
    customer.email = email
    customer.hashed_password = hash_password(password)
    return customer


def test_register_succeeds_for_a_new_email():
    app.dependency_overrides[get_db] = _override_get_db

    try:
        with (
            patch("app.router.customer_routes.get_customer_by_email", return_value=None),
            patch("app.router.customer_routes.create_customer", return_value=_fake_customer()),
        ):
            response = client.post(
                "/register", json={"email": "alice@example.com", "password": "hunter22"}
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_register_rejects_a_duplicate_email():
    app.dependency_overrides[get_db] = _override_get_db

    try:
        with patch("app.router.customer_routes.get_customer_by_email", return_value=_fake_customer()):
            response = client.post(
                "/register", json={"email": "alice@example.com", "password": "hunter22"}
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 409


def test_register_rejects_a_short_password():
    response = client.post("/register", json={"email": "alice@example.com", "password": "short"})

    assert response.status_code == 422


def test_login_succeeds_with_correct_credentials():
    app.dependency_overrides[get_db] = _override_get_db

    try:
        with patch(
            "app.router.customer_routes.get_customer_by_email",
            return_value=_fake_customer(password="hunter22"),
        ):
            response = client.post("/login", json={"email": "alice@example.com", "password": "hunter22"})
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_fails_with_wrong_password():
    app.dependency_overrides[get_db] = _override_get_db

    try:
        with patch(
            "app.router.customer_routes.get_customer_by_email",
            return_value=_fake_customer(password="hunter22"),
        ):
            response = client.post("/login", json={"email": "alice@example.com", "password": "wrong"})
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 401


def test_login_fails_for_unknown_email():
    app.dependency_overrides[get_db] = _override_get_db

    try:
        with patch("app.router.customer_routes.get_customer_by_email", return_value=None):
            response = client.post("/login", json={"email": "nobody@example.com", "password": "hunter22"})
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 401


def test_route_ticket_rejects_missing_token():
    response = client.post("/route-ticket", json={"message": "test ticket"})

    assert response.status_code == 401


def test_route_ticket_rejects_an_admin_token():
    """An admin's JWT has role="admin" -- it must not work here."""
    admin_token = create_access_token(subject="admin", role="admin")

    response = client.post(
        "/route-ticket",
        json={"message": "test ticket"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 401


def test_tickets_mine_rejects_missing_token():
    response = client.get("/tickets/mine")

    assert response.status_code == 401


def test_tickets_mine_returns_only_that_customers_tickets():
    app.dependency_overrides[get_db] = _override_get_db
    customer_token = create_access_token(subject="1", role="customer")

    try:
        with patch("app.router.routes.get_tickets_by_customer", return_value=[]) as mock_get:
            response = client.get("/tickets/mine", headers={"Authorization": f"Bearer {customer_token}"})
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json() == []
    mock_get.assert_called_once()
    assert mock_get.call_args.args[1] == 1
