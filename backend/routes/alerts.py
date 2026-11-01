"""Emergency alert endpoints (all JWT protected)."""
from flask import Blueprint, g, jsonify, request

from extensions import db
from models import EmergencyAlert, NotificationLog, TrustedContact
import notifications as sms
from security import token_required

alerts_bp = Blueprint("alerts", __name__)

ALLOWED_STATUSES = {"active", "acknowledged", "resolved", "cancelled"}


def parse_coords(data):
    """Validate and coerce latitude/longitude from the request body."""
    try:
        lat = float(data.get("latitude"))
        lng = float(data.get("longitude"))
    except (TypeError, ValueError):
        return None, None, "Valid latitude and longitude are required"
    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return None, None, "Latitude must be between -90 and 90 and longitude between -180 and 180"
    return lat, lng, None


def serialize_alert(alert):
    """Serialize an alert together with its SMS notification records + summary."""
    data = alert.to_dict()
    notifications = [n.to_dict() for n in alert.notifications]
    data["notifications"] = notifications
    data["delivery"] = sms.delivery_summary(notifications)
    return data


@alerts_bp.post("")
@token_required
def create_alert():
    data = request.get_json(silent=True) or {}
    lat, lng, error = parse_coords(data)
    if error:
        return jsonify({"error": error}), 400

    status = (data.get("status") or "active").strip().lower()
    if status not in ALLOWED_STATUSES:
        return jsonify({"error": "Invalid status"}), 400

    alert = EmergencyAlert(
        user_id=g.current_user.id,
        latitude=lat,
        longitude=lng,
        status=status,
    )
    db.session.add(alert)
    db.session.commit()  # Persist the alert first so it is never lost.

    # Notify every trusted contact via SMS and record per-recipient delivery.
    contacts = TrustedContact.query.filter_by(user_id=g.current_user.id).all()
    sms.notify_contacts(alert, g.current_user, contacts)

    note = sms.summarize([n.to_dict() for n in alert.notifications])
    return jsonify({
        "alert": serialize_alert(alert),
        "note": note,
    }), 201


@alerts_bp.get("")
@token_required
def list_alerts():
    alerts = (
        EmergencyAlert.query.filter_by(user_id=g.current_user.id)
        .order_by(EmergencyAlert.timestamp.desc())
        .all()
    )
    return jsonify([serialize_alert(a) for a in alerts]), 200


@alerts_bp.get("/<int:alert_id>")
@token_required
def get_alert(alert_id):
    alert = db.session.get(EmergencyAlert, alert_id)
    if not alert or alert.user_id != g.current_user.id:
        return jsonify({"error": "Alert not found"}), 404
    return jsonify(serialize_alert(alert)), 200


@alerts_bp.get("/<int:alert_id>/notifications")
@token_required
def list_notifications(alert_id):
    """Delivery status for every SMS notification attempt of one alert."""
    alert = db.session.get(EmergencyAlert, alert_id)
    if not alert or alert.user_id != g.current_user.id:
        return jsonify({"error": "Alert not found"}), 404
    notifications = [n.to_dict() for n in alert.notifications]
    return jsonify({
        "notifications": notifications,
        "delivery": sms.delivery_summary(notifications),
    }), 200


@alerts_bp.post("/<int:alert_id>/notifications/retry")
@token_required
def retry_notifications(alert_id):
    """Re-send SMS to contacts whose notification failed or is still pending."""
    alert = db.session.get(EmergencyAlert, alert_id)
    if not alert or alert.user_id != g.current_user.id:
        return jsonify({"error": "Alert not found"}), 404

    logs = (
        NotificationLog.query.filter_by(alert_id=alert_id)
        .filter(NotificationLog.status.in_(("failed", "pending")))
        .all()
    )
    if not logs:
        return jsonify({
            "notifications": [n.to_dict() for n in alert.notifications],
            "delivery": sms.delivery_summary([n.to_dict() for n in alert.notifications]),
            "note": "No failed or pending notifications to retry.",
        }), 200

    sms.retry_notifications(alert, g.current_user, logs)
    notifications = [n.to_dict() for n in alert.notifications]
    return jsonify({
        "notifications": notifications,
        "delivery": sms.delivery_summary(notifications),
        "note": sms.summarize(notifications),
    }), 200


@alerts_bp.patch("/<int:alert_id>/status")
@token_required
def update_alert_status(alert_id):
    alert = db.session.get(EmergencyAlert, alert_id)
    if not alert or alert.user_id != g.current_user.id:
        return jsonify({"error": "Alert not found"}), 404

    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "").strip().lower()
    if status not in ALLOWED_STATUSES:
        return jsonify({
            "error": f"Invalid status. Allowed: {', '.join(sorted(ALLOWED_STATUSES))}",
        }), 400

    alert.status = status
    db.session.commit()
    return jsonify(serialize_alert(alert)), 200
