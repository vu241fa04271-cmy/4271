"""Trusted contacts CRUD endpoints (all JWT protected)."""
import re

from flask import Blueprint, g, jsonify, request

from extensions import db
from models import TrustedContact
from security import token_required

contacts_bp = Blueprint("contacts", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_contact(data):
    """Validate contact payload. Returns (values, error_message)."""
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    email = (data.get("email") or "").strip()

    if not name or len(name) > 120:
        return None, "A valid contact name is required (max 120 characters)"
    if not phone or len(phone) > 30:
        return None, "A valid phone number is required (max 30 characters)"
    if email and not EMAIL_RE.match(email):
        return None, "A valid email is required"
    return {"name": name, "phone": phone, "email": email or None}, None


@contacts_bp.get("")
@token_required
def list_contacts():
    contacts = (
        TrustedContact.query.filter_by(user_id=g.current_user.id)
        .order_by(TrustedContact.name.asc())
        .all()
    )
    return jsonify([c.to_dict() for c in contacts]), 200


@contacts_bp.post("")
@token_required
def create_contact():
    data = request.get_json(silent=True) or {}
    values, error = validate_contact(data)
    if error:
        return jsonify({"error": error}), 400

    contact = TrustedContact(user_id=g.current_user.id, **values)
    db.session.add(contact)
    db.session.commit()
    return jsonify(contact.to_dict()), 201


@contacts_bp.put("/<int:contact_id>")
@token_required
def update_contact(contact_id):
    contact = db.session.get(TrustedContact, contact_id)
    if not contact or contact.user_id != g.current_user.id:
        return jsonify({"error": "Contact not found"}), 404

    data = request.get_json(silent=True) or {}
    values, error = validate_contact(data)
    if error:
        return jsonify({"error": error}), 400

    contact.name = values["name"]
    contact.phone = values["phone"]
    contact.email = values["email"]
    db.session.commit()
    return jsonify(contact.to_dict()), 200


@contacts_bp.delete("/<int:contact_id>")
@token_required
def delete_contact(contact_id):
    contact = db.session.get(TrustedContact, contact_id)
    if not contact or contact.user_id != g.current_user.id:
        return jsonify({"error": "Contact not found"}), 404

    db.session.delete(contact)
    db.session.commit()
    return jsonify({"message": "Contact deleted"}), 200
