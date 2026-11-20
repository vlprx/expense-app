
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from passlib.hash import argon2


def hash_password(password: str) -> str:
    """Створює Argon2id-хеш пароля."""
    return argon2.using(type="ID").hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Перевіряє пароль."""
    try:
        return argon2.verify(password, hashed)
    except (ValueError, TypeError):
        return False


def roles_required(*required_roles):
    """Перевіряє роль користувача."""

    def decorator(fn):

        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_roles = claims.get("roles", [])

            if not any(role in user_roles for role in required_roles):
                return jsonify({
                    "error": "forbidden",
                    "message": "Access denied: insufficient privileges",
                }), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def get_current_user_id():
    """Повертає ID авторизованого користувача."""
    return int(get_jwt_identity())


def is_admin():
    """Перевіряє, чи є користувач адміністратором."""
    return "admin" in get_jwt().get("roles", [])
