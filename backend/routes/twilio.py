"""Twilio status callback webhook.

Twilio POSTs message delivery updates here when ``status_callback`` is set on
an outbound SMS. This endpoint updates the matching NotificationLog so the
Alerts page can show real delivered/failed status.

The webhook is intentionally NOT behind JWT auth (Twilio calls it, not a user).
We validate the X-Twilio-Signature header using TWILIO_AUTH_TOKEN unless
TWILIO_VALIDATE_SIGNATURE is false (for local manual testing).
"""
from flask import Blueprint, current_app, request

from extensions import db
from models import NotificationLog
from notifications import TWILIO_STATUS_MAP

twilio_bp = Blueprint("twilio", __name__)


def _is_valid_signature():
    """Validate the Twilio request signature. True if valid or validation disabled."""
    if not current_app.config.get("TWILIO_VALIDATE_SIGNATURE", True):
        return True

    token = current_app.config.get("TWILIO_AUTH_TOKEN", "")
    if not token:
        # No token means SMS is not configured; nothing to validate against.
        return False

    try:
        from twilio.request_validator import RequestValidator
    except ImportError:
        # twilio package not installed -> cannot validate, refuse the callback.
        return False

    validator = RequestValidator(token)
    signature = request.headers.get("X-Twilio-Signature", "")
    # request.form is the raw POST body (Twilio sends application/x-www-form-urlencoded).
    params = request.form.to_dict() if request.form else {}
    return validator.validate(request.url, params, signature)


@twilio_bp.post("/status")
def status_callback():
    if not _is_valid_signature():
        return "Invalid Twilio signature", 403

    sid = request.form.get("MessageSid")
    message_status = (request.form.get("MessageStatus") or "").lower()
    if not sid:
        return "No MessageSid", 400

    log = NotificationLog.query.filter_by(message_sid=sid).first()
    if log is None:
        # Not a message we track (or already cleared); Twilio expects 200 anyway.
        return "OK", 200

    new_status = TWILIO_STATUS_MAP.get(message_status, log.status)
    log.status = new_status

    if new_status == "failed":
        error = (
            request.form.get("ErrorMessage")
            or request.form.get("ErrorCode")
            or "Twilio reported a delivery failure"
        )
        log.error = error
    elif new_status in ("sent", "delivered"):
        # Clear any prior transient error once confirmed accepted/delivered.
        log.error = None

    db.session.commit()
    return "OK", 200
