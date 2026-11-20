
from freezegun import freeze_time

from app.extensions import db
from app.models import User


def test_liveness_check(client):
    with freeze_time("2026-01-01T12:00:00+00:00"):
        response = client.get("/healthz/live")

    assert response.status_code == 200
    assert response.json["status"] == "alive"
    assert response.json["timestamp"] == "2026-01-01T12:00:00+00:00"


def test_readiness_check(client):
    response = client.get("/healthz/ready")

    assert response.status_code == 200
    assert response.json["status"] == "ready"
    assert response.json["database"] == "connected"


def test_register_and_login(client):
    register_response = client.post(
        "/register",
        json={
            "name": "newuser",
            "password": "TestPass123!",
        },
    )

    assert register_response.status_code == 201
    assert register_response.json["user"]["role"] == "user"

    login_response = client.post(
        "/login",
        json={
            "name": "newuser",
            "password": "TestPass123!",
        },
    )

    assert login_response.status_code == 200
    assert login_response.json["token_type"] == "Bearer"
    assert login_response.json["access_token"]


def test_login_with_wrong_password(client, create_user):
    create_user("wrongpass")

    response = client.post(
        "/login",
        json={
            "name": "wrongpass",
            "password": "Incorrect123!",
        },
    )

    assert response.status_code == 401


def test_user_cannot_access_without_token(client, create_user):
    user = create_user("privateuser")

    response = client.get(f"/user/{user['id']}")

    assert response.status_code == 401


def test_user_can_access_own_profile(client, create_user, login):
    user = create_user("owner")
    headers = login("owner")

    response = client.get(
        f"/user/{user['id']}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json["name"] == "owner"


def test_user_cannot_access_foreign_profile(client, create_user, login):
    create_user("firstuser")
    second_user = create_user("seconduser")
    headers = login("firstuser")

    response = client.get(
        f"/user/{second_user['id']}",
        headers=headers,
    )

    assert response.status_code == 404


def test_user_cannot_list_all_users(client, create_user, login):
    create_user("regular")
    headers = login("regular")

    response = client.get("/users", headers=headers)

    assert response.status_code == 403


def test_auditor_can_list_users(client, create_user, login, app):
    auditor = create_user("auditor")

    with app.app_context():
        user = db.session.get(User, auditor["id"])
        user.role = "auditor"
        db.session.commit()

    headers = login("auditor")
    response = client.get("/users", headers=headers)

    assert response.status_code == 200
    assert any(item["name"] == "auditor" for item in response.json)


def test_auditor_cannot_create_category(client, create_user, login, app):
    auditor = create_user("readonly")

    with app.app_context():
        user = db.session.get(User, auditor["id"])
        user.role = "auditor"
        db.session.commit()

    headers = login("readonly")

    response = client.post(
        "/category",
        json={"name": "Forbidden category"},
        headers=headers,
    )

    assert response.status_code == 403


def test_admin_can_list_users(client, create_user, login, app):
    admin = create_user("administrator")

    with app.app_context():
        user = db.session.get(User, admin["id"])
        user.role = "admin"
        db.session.commit()

    headers = login("administrator")
    response = client.get("/users", headers=headers)

    assert response.status_code == 200
    assert any(item["name"] == "administrator" for item in response.json)
