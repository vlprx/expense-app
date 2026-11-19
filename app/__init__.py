
import os

from flask import Flask

from app.extensions import db, migrate


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://expense_user:expense_password@localhost:5432/expense_db",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)

    from app import models  # noqa: F401
    from app.views import register_routes

    register_routes(app)

    return app
