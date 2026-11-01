"""Application factory and entry point for the Women's Safety backend."""
import os

from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config, config_by_name
from extensions import cors, db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Trust proxy headers (X-Forwarded-Proto/Host) so request.url reflects the
    # public https URL behind a tunnel (ngrok/cloudflare) — needed for Twilio
    # status-callback signature validation.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Ensure the SQLite instance folder exists when using the default file db.
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite:///") and ":memory:" not in db_uri:
        db_path = db_uri.replace("sqlite:///", "", 1)
        instance_dir = os.path.dirname(db_path) or "instance"
        os.makedirs(instance_dir, exist_ok=True)

    db.init_app(app)

    cors_origins = app.config.get("CORS_ORIGINS", "*")
    if cors_origins == "*":
        origins = "*"
    else:
        origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
    cors.init_app(app, resources={r"/*": {"origins": origins}}, supports_credentials=True)

    # Register blueprints (imported here to avoid circular imports).
    from routes.alerts import alerts_bp
    from routes.auth import auth_bp
    from routes.contacts import contacts_bp
    from routes.location import location_bp
    from routes.twilio import twilio_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(contacts_bp, url_prefix="/api/contacts")
    app.register_blueprint(alerts_bp, url_prefix="/api/alerts")
    app.register_blueprint(location_bp, url_prefix="/api/location")
    app.register_blueprint(twilio_bp, url_prefix="/api/twilio")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "women-safety-backend"}), 200

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def server_error(_e):
        return jsonify({"error": "Internal server error"}), 500

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    env = os.environ.get("FLASK_ENV", "development")
    app = create_app(config_by_name.get(env, Config))
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", True))
