
import os

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": os.getenv(
            "TEST_DATABASE_URL",
            "sqlite://",
        ),
        "JWT_SECRET_KEY": "test-secret-key-for-expense-app-ci",
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def create_user(client):
    def _create_user(name, password="TestPass123!"):
        response = client.post(
            "/register",
            json={"name": name, "password": password},
        )
        assert response.status_code == 201
        return response.get_json()["user"]

    return _create_user


@pytest.fixture
def login(client):
    def _login(name, password="TestPass123!"):
        response = client.post(
            "/login",
            json={"name": name, "password": password},
        )
        assert response.status_code == 200
        token = response.get_json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _login
