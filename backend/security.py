"""Authentication helpers: JWT creation and a route guard decorator."""
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request

from extensions import db
from models import User


def create_token(user):
    """Return a signed JWT for the given user model instance."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "name": user.name,
        "email": user.email,
        "iat": now,
        "exp": now + timedelta(hours=current_app.config["JWT_EXPIRATION_HOURS"]),
    }
    token = jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")
    # PyJWT >= 2 returns a str already; keep this for safety with older builds.
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def token_required(f):
    """Protect a route. Reads a Bearer token and exposes g.current_user."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return jsonify({"error": "Authentication token is missing"}), 401

        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"],
            )
            user_id = int(payload.get("sub", 0))
            user = db.session.get(User, user_id)
            if user is None:
                return jsonify({"error": "Invalid token"}), 401
            g.current_user = user
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except (jwt.InvalidTokenError, ValueError, TypeError):
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated
