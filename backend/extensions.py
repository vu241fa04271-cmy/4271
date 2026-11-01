"""Shared Flask extensions.

Kept in a separate module so models and routes can import the ``db`` object
without creating a circular import with the application factory in app.py.
"""
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
cors = CORS()
