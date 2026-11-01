"""Application configuration.

Sensitive values are read from environment variables (see .env.example).
The defaults here are intentionally obvious so that they fail loudly in
production rather than silently shipping a weak secret.
"""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration shared by all environments."""

    # --- Flask / security ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-dev-secret-change-me")
    JWT_EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", "24"))

    # --- Database ---
    # Stored in backend/instance/ by default so it survives restarts.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "instance", "womens_safety.db"
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- CORS ---
    # Comma-separated list of allowed origins for production.
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    # --- Twilio (SMS notifications) ---
    # All values come from environment variables and are NEVER exposed to the
    # frontend. Leave blank to disable SMS sending; the app then records alerts
    # and marks notifications as failed with a clear "not configured" reason.
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
    # A Twilio phone number in E.164 format, e.g. +12345678900
    TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")
    # Public URL of this backend so Twilio can call back with delivery status.
    # e.g. https://your-tunnel.ngrok-free.app  (no trailing slash)
    TWILIO_STATUS_CALLBACK_URL = os.environ.get("TWILIO_STATUS_CALLBACK_URL", "")
    # Validate the X-Twilio-Signature header on the status webhook. Disable only
    # for local manual testing (keep true in production). Requires ProxyFix to be
    # effective behind a tunnel so request.url reflects the public https URL.
    TWILIO_VALIDATE_SIGNATURE = os.environ.get("TWILIO_VALIDATE_SIGNATURE", "true").lower() == "true"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret"
    # Force Twilio OFF in tests so behavior is deterministic even if the dev
    # has real credentials in backend/.env (load_dotenv runs at import time).
    TWILIO_ACCOUNT_SID = ""
    TWILIO_AUTH_TOKEN = ""
    TWILIO_PHONE_NUMBER = ""
    TWILIO_STATUS_CALLBACK_URL = ""
    TWILIO_VALIDATE_SIGNATURE = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
