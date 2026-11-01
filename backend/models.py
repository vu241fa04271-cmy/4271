"""Database models for the Women's Safety Emergency Alert System."""
from datetime import datetime, timezone

from extensions import db


def _utcnow():
    """Timezone-aware UTC 'now' used as a default column value."""
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    contacts = db.relationship(
        "TrustedContact",
        backref="user",
        cascade="all, delete-orphan",
        lazy=True,
    )
    alerts = db.relationship(
        "EmergencyAlert",
        backref="user",
        cascade="all, delete-orphan",
        lazy=True,
    )
    locations = db.relationship(
        "Location",
        backref="user",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TrustedContact(db.Model):
    __tablename__ = "trusted_contacts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(180), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email or "",
        }


class EmergencyAlert(db.Model):
    __tablename__ = "emergency_alerts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow, nullable=False, index=True)
    # active | acknowledged | resolved | cancelled
    status = db.Column(db.String(20), default="active", nullable=False)

    notifications = db.relationship(
        "NotificationLog",
        backref="alert",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "status": self.status,
        }


class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class NotificationLog(db.Model):
    """One row per SMS notification attempt for an emergency alert."""

    __tablename__ = "notification_logs"

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(
        db.Integer,
        db.ForeignKey("emergency_alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Contact is optional (SET NULL) so the log survives a contact being deleted.
    contact_id = db.Column(
        db.Integer,
        db.ForeignKey("trusted_contacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    recipient_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    # pending | sent | delivered | failed
    status = db.Column(db.String(20), default="pending", nullable=False)
    message_sid = db.Column(db.String(64), nullable=True)
    error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "contact_id": self.contact_id,
            "recipient_name": self.recipient_name,
            "phone": self.phone,
            "status": self.status,
            "message_sid": self.message_sid,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
