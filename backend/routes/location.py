"""Location tracking endpoints (all JWT protected)."""
from flask import Blueprint, g, jsonify, request

from extensions import db
from models import Location
from security import token_required

location_bp = Blueprint("location", __name__)


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


@location_bp.post("")
@token_required
def save_location():
    data = request.get_json(silent=True) or {}
    lat, lng, error = parse_coords(data)
    if error:
        return jsonify({"error": error}), 400

    loc = Location(user_id=g.current_user.id, latitude=lat, longitude=lng)
    db.session.add(loc)
    db.session.commit()
    return jsonify(loc.to_dict()), 201


@location_bp.get("/latest")
@token_required
def latest_location():
    loc = (
        Location.query.filter_by(user_id=g.current_user.id)
        .order_by(Location.timestamp.desc())
        .first()
    )
    if not loc:
        return jsonify({"error": "No location recorded yet"}), 404
    return jsonify(loc.to_dict()), 200
