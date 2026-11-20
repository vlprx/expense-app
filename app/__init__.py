
import os

from flask import Flask

from app.extensions import db, jwt, migrate


def create_app(test_config=None):
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://expense_user:expense_password@localhost:5432/expense_db",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY",
        "dev-secret-key-change-before-production",
    )
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from app import models  # noqa: F401
    from app.routes import register_auth_routes
    from app.views import register_routes

    register_routes(app)
    register_auth_routes(app)

    return app
