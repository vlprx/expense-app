
from flask import jsonify, request
from flask_jwt_extended import create_access_token

from app.auth import hash_password, verify_password
from app.extensions import db
from app.models import User


def register_auth_routes(app):

    # Реєстрація нового користувача
    @app.route("/register", methods=["POST"])
    def register():
        data = request.get_json(silent=True) or {}

        name = data.get("name")
        password = data.get("password")

        if not isinstance(name, str) or not name.strip():
            return jsonify({
                "error": "validation_error",
                "message": "Name is required",
            }), 400

        if not isinstance(password, str) or len(password) < 8:
            return jsonify({
                "error": "validation_error",
                "message": "Password must contain at least 8 characters",
            }), 400

        name = name.strip()

        existing_user = User.query.filter_by(name=name).first()

        if existing_user:
            return jsonify({
                "error": "user_exists",
                "message": "User with this name already exists",
            }), 409

        user = User(
            name=name,
            password_hash=hash_password(password),
            role="user",
        )

        db.session.add(user)
        db.session.flush()

        # Створення рахунку для нового користувача
        from app.models import Account

        account = Account(
            user_id=user.id,
        )

        db.session.add(account)
        db.session.commit()

        return jsonify({
            "message": "User registered successfully",
            "user": {
                "id": user.id,
                "name": user.name,
                "role": user.role,
            },
        }), 201

    # Авторизація користувача
    @app.route("/login", methods=["POST"])
    def login():
        data = request.get_json(silent=True) or {}

        name = data.get("name")
        password = data.get("password")

        if not isinstance(name, str) or not isinstance(password, str):
            return jsonify({
                "error": "validation_error",
                "message": "Name and password are required",
            }), 400

        user = User.query.filter_by(name=name.strip()).first()

        if (
            user is None
            or not user.password_hash
            or not verify_password(password, user.password_hash)
        ):
            return jsonify({
                "error": "invalid_credentials",
                "message": "Invalid name or password",
            }), 401

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "roles": [user.role],
                "role": user.role,
            },
        )

        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "Bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "role": user.role,
            },
        }), 200
