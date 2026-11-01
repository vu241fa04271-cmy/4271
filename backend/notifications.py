"""Twilio SMS notification service for emergency alerts.

All Twilio credentials live in backend environment variables (see config.py)
and are never sent to the React frontend. The frontend only ever receives the
*status* of each notification attempt (sent / delivered / failed + error text).
"""
from datetime import timezone

from flask import current_app

from extensions import db
from models import NotificationLog

# Used by the Twilio status callback webhook to map Twilio message statuses onto
# our internal NotificationLog.status values.
TWILIO_STATUS_MAP = {
    "queued": "sent",
    "sending": "sent",
    "sent": "sent",
    "delivered": "delivered",
    "read": "delivered",
    "failed": "failed",
    "undelivered": "failed",
    "canceled": "failed",
}


def _fmt_timestamp(ts):
    if ts is None:
        return "unknown"
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def build_message(user_name, alert):
    """Compose the SMS body: name, emergency message, timestamp, coords, map link."""
    map_link = f"https://www.google.com/maps?q={alert.latitude},{alert.longitude}"
    return (
        "[SAFEHER EMERGENCY SOS]\n"
        f"{user_name} triggered an emergency alert.\n\n"
        f"Time: {_fmt_timestamp(alert.timestamp)}\n"
        f"Location: {alert.latitude}, {alert.longitude}\n"
        f"Map: {map_link}\n\n"
        "If you are a trusted contact, please reach out or contact local "
        "emergency services (112 in India)."
    )


def is_configured():
    """True only when all three required Twilio credentials are set."""
    return bool(
        current_app.config.get("TWILIO_ACCOUNT_SID")
        and current_app.config.get("TWILIO_AUTH_TOKEN")
        and current_app.config.get("TWILIO_PHONE_NUMBER")
    )


def _get_client():
    """Create a Twilio client. Patchable in tests via notifications._get_client.

    The Twilio import is lazy so the application still boots if the ``twilio``
    package is not installed; SMS sending then fails with a clear message.
    """
    from twilio.rest import Client

    return Client(
        current_app.config["TWILIO_ACCOUNT_SID"],
        current_app.config["TWILIO_AUTH_TOKEN"],
    )


def _send_one(to_number, body):
    """Send a single SMS. Returns (status, message_sid, error).

    Raises TwilioRestException on API errors (e.g. invalid number); other
    exceptions (network/timeout) propagate to the caller which handles them.
    """
    from_number = current_app.config["TWILIO_PHONE_NUMBER"]
    callback_url = current_app.config.get("TWILIO_STATUS_CALLBACK_URL")
    kwargs = {"body": body, "from_": from_number, "to": to_number}
    if callback_url:
        # Trailing slash is harmless; Twilio appends nothing.
        kwargs["status_callback"] = callback_url.rstrip("/") + "/api/twilio/status"
    client = _get_client()
    message = client.messages.create(**kwargs)
    # Accepted by Twilio immediately (status queued/sending/sent).
    if message.status in ("failed", "undelivered", "canceled"):
        return "failed", message.sid, (message.error_message or "Twilio reported a failure")
    return "sent", message.sid, None


def _attempt(log, body, configured):
    """Try to deliver one SMS for an existing NotificationLog, updating it in place."""
    if not configured:
        log.status = "failed"
        log.message_sid = None
        log.error = (
            "Twilio is not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, "
            "and TWILIO_PHONE_NUMBER in backend/.env to enable SMS."
        )
        return
    try:
        status, sid, error = _send_one(log.phone, body)
        log.status = status
        log.message_sid = sid
        log.error = error
    except Exception as exc:
        log.status = "failed"
        log.message_sid = None
        # Surface a clearer message for Twilio API errors (invalid number, etc.).
        try:
            from twilio.base.exceptions import TwilioRestException

            if isinstance(exc, TwilioRestException):
                code = getattr(exc, "code", None)
                msg = getattr(exc, "msg", None) or str(exc)
                log.error = f"Twilio error {code}: {msg}" if code else f"Twilio error: {msg}"
                return
        except ImportError:
            pass
        log.error = f"Failed to send SMS: {exc}"


def notify_contacts(alert, user, contacts):
    """Create a NotificationLog per contact and send each an SMS.

    Returns the list of serialized notification dicts. The alert must already be
    committed so its id is available. Commits the notification logs at the end.
    """
    results = []
    if not contacts:
        return results

    body = build_message(user.name, alert)
    configured = is_configured()

    for contact in contacts:
        log = NotificationLog(
            alert_id=alert.id,
            contact_id=contact.id,
            recipient_name=contact.name,
            phone=contact.phone,
            status="pending",
        )
        db.session.add(log)
        db.session.flush()  # assign log.id before sending
        _attempt(log, body, configured)
        results.append(log.to_dict())

    db.session.commit()
    return results


def retry_notifications(alert, user, logs):
    """Re-attempt sending for the given (already persisted) NotificationLogs."""
    body = build_message(user.name, alert)
    configured = is_configured()
    for log in logs:
        _attempt(log, body, configured)
    db.session.commit()
    return [log.to_dict() for log in logs]


def delivery_summary(notifications):
    """Aggregate counts for a list of serialized notification dicts."""
    return {
        "total": len(notifications),
        "sent": sum(1 for n in notifications if n["status"] == "sent"),
        "delivered": sum(1 for n in notifications if n["status"] == "delivered"),
        "failed": sum(1 for n in notifications if n["status"] == "failed"),
        "pending": sum(1 for n in notifications if n["status"] == "pending"),
    }


def summarize(notifications):
    """Human-readable summary used in the create-alert response and toasts."""
    if not notifications:
        return (
            "Alert recorded, but you have no trusted contacts to notify. "
            "Add contacts and call emergency services (112) directly."
        )
    s = delivery_summary(notifications)
    ok = s["sent"] + s["delivered"]
    if s["failed"] == s["total"]:
        return (
            f"Alert recorded. SMS delivery failed for all {s['failed']} "
            "contact(s). Please call emergency services (112) directly."
        )
    parts = [f"SMS sent to {ok} of {s['total']} contact(s)."]
    if s["failed"]:
        parts.append(f"{s['failed']} failed.")
    parts.append("Please call emergency services (112) to confirm help is on the way.")
    return " ".join(parts)
