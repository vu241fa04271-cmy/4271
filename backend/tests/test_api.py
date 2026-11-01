"""Basic backend API tests.

Run from the backend folder:
    pip install -r requirements-dev.txt
    pytest -q

Uses an in-memory SQLite database so no file artifacts are created.
"""
import os
import sys

import pytest

# Make the backend package importable when running from the tests folder.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from config import TestingConfig  # noqa: E402
from extensions import db as _db  # noqa: E402


@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        _db.create_all()
    yield app
    with app.app_context():
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def register_and_login(client, email="alice@example.com", password="secret123"):
    r = client.post("/api/auth/register", json={
        "name": "Alice", "email": email, "password": password,
    })
    assert r.status_code == 201, r.get_json()
    token = r.get_json()["token"]
    return token


# --- auth --------------------------------------------------------------------

def test_register_success(client):
    r = client.post("/api/auth/register", json={
        "name": "Bob", "email": "bob@example.com", "password": "secret123",
    })
    assert r.status_code == 201
    data = r.get_json()
    assert "token" in data
    assert data["user"]["email"] == "bob@example.com"


def test_register_duplicate_email(client):
    register_and_login(client, email="dup@example.com")
    r = client.post("/api/auth/register", json={
        "name": "Dup", "email": "dup@example.com", "password": "secret123",
    })
    assert r.status_code == 409


def test_register_validation(client):
    r = client.post("/api/auth/register", json={"name": "", "email": "bad", "password": "12"})
    assert r.status_code == 400


def test_login_success(client):
    register_and_login(client, email="login@example.com")
    r = client.post("/api/auth/login", json={
        "email": "login@example.com", "password": "secret123",
    })
    assert r.status_code == 200
    assert "token" in r.get_json()


def test_login_wrong_password(client):
    register_and_login(client, email="wrongpw@example.com")
    r = client.post("/api/auth/login", json={
        "email": "wrongpw@example.com", "password": "nope",
    })
    assert r.status_code == 401


def test_me_requires_token(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_returns_user(client):
    token = register_and_login(client)
    r = client.get("/api/auth/me", headers=auth_header(token))
    assert r.status_code == 200
    assert r.get_json()["email"] == "alice@example.com"


# --- contacts ----------------------------------------------------------------

def test_contacts_crud(client):
    token = register_and_login(client)

    # create
    r = client.post("/api/contacts", headers=auth_header(token), json={
        "name": "Mom", "phone": "+919800000001", "email": "mom@example.com",
    })
    assert r.status_code == 201
    cid = r.get_json()["id"]

    # list
    r = client.get("/api/contacts", headers=auth_header(token))
    assert r.status_code == 200
    assert len(r.get_json()) == 1

    # update
    r = client.put(f"/api/contacts/{cid}", headers=auth_header(token), json={
        "name": "Mother", "phone": "+919800000002", "email": "mother@example.com",
    })
    assert r.status_code == 200
    assert r.get_json()["name"] == "Mother"

    # delete
    r = client.delete(f"/api/contacts/{cid}", headers=auth_header(token))
    assert r.status_code == 200
    assert client.get("/api/contacts", headers=auth_header(token)).get_json() == []


def test_contacts_isolated_between_users(client):
    t1 = register_and_login(client, email="user1@example.com")
    t2 = register_and_login(client, email="user2@example.com")
    client.post("/api/contacts", headers=auth_header(t1), json={
        "name": "OnlyOne", "phone": "111", "email": "",
    })
    r = client.get("/api/contacts", headers=auth_header(t2))
    assert r.status_code == 200
    assert r.get_json() == []


def test_contacts_validation(client):
    token = register_and_login(client)
    r = client.post("/api/contacts", headers=auth_header(token), json={
        "name": "", "phone": "", "email": "",
    })
    assert r.status_code == 400


# --- alerts ------------------------------------------------------------------

def test_alert_lifecycle(client):
    token = register_and_login(client)

    r = client.post("/api/alerts", headers=auth_header(token), json={
        "latitude": 12.9716, "longitude": 77.5946,
    })
    assert r.status_code == 201
    body = r.get_json()
    aid = body["alert"]["id"]
    assert body["alert"]["status"] == "active"
    # No trusted contacts on this account -> no notifications sent.
    assert body["alert"]["notifications"] == []
    assert body["alert"]["delivery"]["total"] == 0
    assert "112" in body["note"]

    # list
    r = client.get("/api/alerts", headers=auth_header(token))
    assert r.status_code == 200
    assert len(r.get_json()) == 1

    # get one
    r = client.get(f"/api/alerts/{aid}", headers=auth_header(token))
    assert r.status_code == 200

    # update status
    r = client.patch(f"/api/alerts/{aid}/status", headers=auth_header(token), json={
        "status": "resolved",
    })
    assert r.status_code == 200
    assert r.get_json()["status"] == "resolved"


def test_alert_invalid_coords(client):
    token = register_and_login(client)
    r = client.post("/api/alerts", headers=auth_header(token), json={
        "latitude": 999, "longitude": 0,
    })
    assert r.status_code == 400


def test_alert_requires_token(client):
    r = client.post("/api/alerts", json={"latitude": 0, "longitude": 0})
    assert r.status_code == 401


# --- location ----------------------------------------------------------------

def test_location_save_and_latest(client):
    token = register_and_login(client)

    r = client.post("/api/location", headers=auth_header(token), json={
        "latitude": 28.6139, "longitude": 77.2090,
    })
    assert r.status_code == 201

    r = client.get("/api/location/latest", headers=auth_header(token))
    assert r.status_code == 200
    body = r.get_json()
    assert body["latitude"] == 28.6139
    assert body["longitude"] == 77.2090


def test_location_latest_none(client):
    token = register_and_login(client)
    r = client.get("/api/location/latest", headers=auth_header(token))
    assert r.status_code == 404


# --- misc --------------------------------------------------------------------

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"
