"""Tests for Twilio SMS notification behavior on SOS alerts.

Twilio is never called for real: the Twilio client is monkeypatched. With no
credentials configured, notifications are recorded as failed with a clear
reason; with credentials + a mocked client, notifications are recorded as sent.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from config import TestingConfig  # noqa: E402
from extensions import db as _db  # noqa: E402
from models import NotificationLog  # noqa: E402
import notifications as sms  # noqa: E402
from twilio.base.exceptions import TwilioRestException  # noqa: E402


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


def register_and_login(client, email="notif@example.com"):
    r = client.post("/api/auth/register", json={"name": "Notifier", "email": email, "password": "secret123"})
    assert r.status_code == 201, r.get_json()
    return r.get_json()["token"]


def add_contact(client, token, name, phone):
    r = client.post("/api/contacts", headers=auth_header(token), json={"name": name, "phone": phone})
    assert r.status_code == 201, r.get_json()
    return r.get_json()["id"]


def trigger_alert(client, token):
    r = client.post("/api/alerts", headers=auth_header(token), json={"latitude": 12.9716, "longitude": 77.5946})
    return r


def _enable_twilio(app):
    app.config["TWILIO_ACCOUNT_SID"] = "AC_test"
    app.config["TWILIO_AUTH_TOKEN"] = "test_token"
    app.config["TWILIO_PHONE_NUMBER"] = "+10000000000"
    app.config["TWILIO_STATUS_CALLBACK_URL"] = ""
    app.config["TWILIO_VALIDATE_SIGNATURE"] = False


class FakeMessage:
    def __init__(self, sid, status="queued"):
        self.sid = sid
        self.status = status
        self.error_message = None


class FakeMessages:
    def __init__(self, fail_numbers):
        self.fail_numbers = fail_numbers or set()
        self.count = 0

    def create(self, body=None, from_=None, to=None, status_callback=None, **_):
        self.count += 1
        if to in self.fail_numbers:
            raise TwilioRestException(status=400, uri="https://api.twilio.com", msg="number invalid", code=21211)
        return FakeMessage(f"SM_FAKE_{self.count}", status="queued")


class FakeClient:
    def __init__(self, fail_numbers=None):
        self.messages = FakeMessages(fail_numbers)


# --- not configured -------------------------------------------------------

def test_alert_without_contacts_has_no_notifications(client):
    token = register_and_login(client)
    r = trigger_alert(client, token)
    assert r.status_code == 201
    body = r.get_json()
    assert body["alert"]["notifications"] == []
    assert body["alert"]["delivery"]["total"] == 0
    assert "no trusted contacts" in body["note"].lower()


def test_notifications_failed_when_twilio_not_configured(client):
    token = register_and_login(client)
    add_contact(client, token, "Mom", "+919800000001")
    add_contact(client, token, "Dad", "+919800000002")

    r = trigger_alert(client, token)
    assert r.status_code == 201
    body = r.get_json()
    notifs = body["alert"]["notifications"]
    assert len(notifs) == 2
    assert all(n["status"] == "failed" for n in notifs)
    assert body["alert"]["delivery"]["failed"] == 2
    assert all("not configured" in (n["error"] or "") for n in notifs)
    assert "failed" in body["note"].lower()


def test_notifications_endpoint_returns_logs(client):
    token = register_and_login(client)
    add_contact(client, token, "Mom", "+919800000001")
    trigger_alert(client, token)

    r = client.get("/api/alerts", headers=auth_header(token))
    alert_id = r.get_json()[0]["id"]

    r = client.get(f"/api/alerts/{alert_id}/notifications", headers=auth_header(token))
    assert r.status_code == 200
    assert len(r.get_json()["notifications"]) == 1
    assert r.get_json()["delivery"]["failed"] == 1


def test_retry_endpoint_re_attempts_failed(client):
    token = register_and_login(client)
    add_contact(client, token, "Mom", "+919800000001")
    trigger_alert(client, token)

    alert_id = client.get("/api/alerts", headers=auth_header(token)).get_json()[0]["id"]

    r = client.post(f"/api/alerts/{alert_id}/notifications/retry", headers=auth_header(token))
    assert r.status_code == 200
    # Still not configured, so they remain failed but the retry endpoint ran.
    assert r.get_json()["delivery"]["failed"] == 1


def test_retry_with_nothing_to_retry(client):
    token = register_and_login(client)
    add_contact(client, token, "Mom", "+919800000001")
    trigger_alert(client, token)
    alert_id = client.get("/api/alerts", headers=auth_header(token)).get_json()[0]["id"]

    # First retry attempts the one failed log.
    client.post(f"/api/alerts/{alert_id}/notifications/retry", headers=auth_header(token))
    # Second retry: still failed (not configured), but endpoint handles gracefully.
    r = client.post(f"/api/alerts/{alert_id}/notifications/retry", headers=auth_header(token))
    assert r.status_code == 200


# --- configured + mocked client -------------------------------------------

def test_notifications_sent_with_mocked_twilio(app, client, monkeypatch):
    _enable_twilio(app)
    token = register_and_login(client)
    add_contact(client, token, "Mom", "+919800000001")
    add_contact(client, token, "Dad", "+919800000002")

    fake = FakeClient(fail_numbers={"+919800000002"})
    monkeypatch.setattr(sms, "_get_client", lambda: fake)

    r = trigger_alert(client, token)
    assert r.status_code == 201
    body = r.get_json()
    notifs = body["alert"]["notifications"]
    assert len(notifs) == 2

    by_phone = {n["phone"]: n for n in notifs}
    assert by_phone["+919800000001"]["status"] == "sent"
    assert by_phone["+919800000001"]["message_sid"].startswith("SM_FAKE_")
    assert by_phone["+919800000002"]["status"] == "failed"
    assert "21211" in (by_phone["+919800000002"]["error"] or "")

    assert body["alert"]["delivery"]["sent"] == 1
    assert body["alert"]["delivery"]["failed"] == 1
    assert "sent to 1 of 2" in body["note"]


def test_retry_succeeds_after_config(app, client, monkeypatch):
    # First alert while not configured -> failed.
    token = register_and_login(client)
    add_contact(client, token, "Mom", "+919800000001")
    trigger_alert(client, token)
    alert_id = client.get("/api/alerts", headers=auth_header(token)).get_json()[0]["id"]

    # Now configure Twilio and mock a successful send, then retry.
    _enable_twilio(app)
    fake = FakeClient()
    monkeypatch.setattr(sms, "_get_client", lambda: fake)

    r = client.post(f"/api/alerts/{alert_id}/notifications/retry", headers=auth_header(token))
    assert r.status_code == 200
    assert r.get_json()["delivery"]["sent"] == 1
    assert r.get_json()["delivery"]["failed"] == 0


# --- status callback webhook -----------------------------------------------

def test_status_webhook_updates_log(app, client, monkeypatch):
    _enable_twilio(app)
    token = register_and_login(client)
    add_contact(client, token, "Mom", "+919800000001")
    fake = FakeClient()
    monkeypatch.setattr(sms, "_get_client", lambda: fake)

    trigger_alert(client, token)
    alert_id = client.get("/api/alerts", headers=auth_header(token)).get_json()[0]["id"]

    # Direct model queries need an app context (the test client pushes one only
    # during a request).
    with app.app_context():
        log = NotificationLog.query.filter_by(alert_id=alert_id).first()
        assert log.status == "sent"
        sid = log.message_sid
        log_id = log.id

    # Twilio posts a delivery update (signature validation disabled in _enable_twilio).
    r = client.post(
        "/api/twilio/status",
        data={"MessageSid": sid, "MessageStatus": "delivered"},
    )
    assert r.status_code == 200

    with app.app_context():
        refreshed = _db.session.get(NotificationLog, log_id)
        assert refreshed.status == "delivered"
        assert refreshed.error is None


def test_status_webhook_rejects_bad_signature(app, client):
    app.config["TWILIO_VALIDATE_SIGNATURE"] = True
    app.config["TWILIO_AUTH_TOKEN"] = ""  # no token -> cannot validate
    r = client.post("/api/twilio/status", data={"MessageSid": "SM_x", "MessageStatus": "delivered"})
    assert r.status_code == 403
