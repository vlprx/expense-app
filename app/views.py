
from datetime import UTC, datetime

from flask import jsonify, request
from flask_jwt_extended import get_jwt
from marshmallow import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.auth import get_current_user_id, roles_required
from app.extensions import db
from app.models import Account, Category, Record, User
from app.schemas import CategorySchema, DepositSchema, RecordSchema


def validation_error(error):
    return jsonify({
        "error": "validation_error",
        "messages": error.messages,
    }), 400


def forbidden():
    return jsonify({
        "error": "forbidden",
        "message": "Access denied",
    }), 403


def not_found(message):
    return jsonify({"error": message}), 404


def current_role():
    return get_jwt().get("role", "user")


def register_routes(app):

    # ==================== HEALTH ====================

    @app.route("/healthz/live", methods=["GET"])
    def liveness_check():
        return jsonify({
            "status": "alive",
            "timestamp": datetime.now(UTC).isoformat(),
        }), 200

    @app.route("/healthz/ready", methods=["GET"])
    def readiness_check():
        try:
            db.session.execute(text("SELECT 1"))
            return jsonify({
                "status": "ready",
                "database": "connected",
                "timestamp": datetime.now(UTC).isoformat(),
            }), 200
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({
                "status": "not_ready",
                "database": "disconnected",
                "timestamp": datetime.now(UTC).isoformat(),
            }), 503

    # ==================== USERS ====================

    @app.route("/users", methods=["GET"])
    @roles_required("auditor", "admin")
    def get_users():
        users = User.query.all()

        return jsonify([
            {
                "id": user.id,
                "name": user.name,
                "role": user.role,
            }
            for user in users
        ]), 200

    @app.route("/user/<int:user_id>", methods=["GET"])
    @roles_required("user", "auditor", "admin")
    def get_user(user_id):
        if current_role() == "user" and user_id != get_current_user_id():
            return not_found("User not found")

        user = db.session.get(User, user_id)

        if user is None:
            return not_found("User not found")

        return jsonify({
            "id": user.id,
            "name": user.name,
            "role": user.role,
            "account": {
                "id": user.account.id,
                "balance": str(user.account.balance),
            } if user.account else None,
        }), 200

    @app.route("/user/<int:user_id>", methods=["DELETE"])
    @roles_required("admin")
    def delete_user(user_id):
        user = db.session.get(User, user_id)

        if user is None:
            return not_found("User not found")

        db.session.delete(user)
        db.session.commit()

        return "", 204

    # Адміністратор може змінювати ролі користувачів
    @app.route("/user/<int:user_id>/role", methods=["PATCH"])
    @roles_required("admin")
    def update_user_role(user_id):
        user = db.session.get(User, user_id)

        if user is None:
            return not_found("User not found")

        data = request.get_json(silent=True) or {}
        new_role = data.get("role")

        if new_role not in ("user", "auditor", "admin"):
            return jsonify({
                "error": "validation_error",
                "message": "Role must be user, auditor or admin",
            }), 400

        user.role = new_role
        db.session.commit()

        return jsonify({
            "message": "User role updated",
            "user": {
                "id": user.id,
                "name": user.name,
                "role": user.role,
            },
        }), 200

    # ==================== CATEGORIES ====================

    @app.route("/category", methods=["GET"])
    @roles_required("user", "auditor", "admin")
    def get_categories():
        query = Category.query

        if current_role() == "user":
            user_id = get_current_user_id()
            query = query.filter(
                (Category.user_id == user_id)
                | (Category.user_id.is_(None))
            )

        categories = query.all()

        return jsonify([
            {
                "id": category.id,
                "name": category.name,
                "user_id": category.user_id,
            }
            for category in categories
        ]), 200

    # Особиста категорія користувача
    @app.route("/category", methods=["POST"])
    @roles_required("user", "admin")
    def create_category():
        try:
            data = CategorySchema().load(
                request.get_json(silent=True) or {}
            )
        except ValidationError as error:
            return validation_error(error)

        payload = request.get_json(silent=True) or {}

        if current_role() == "user":
            owner_id = get_current_user_id()
        else:
            owner_id = payload.get("user_id", get_current_user_id())

            if not isinstance(owner_id, int):
                return jsonify({
                    "error": "validation_error",
                    "message": "user_id must be an integer",
                }), 400

            if db.session.get(User, owner_id) is None:
                return not_found("User not found")

        category = Category(
            name=data["name"].strip(),
            user_id=owner_id,
        )

        db.session.add(category)
        db.session.commit()

        return jsonify({
            "id": category.id,
            "name": category.name,
            "user_id": category.user_id,
        }), 201

    # Глобальні категорії може створювати лише адміністратор
    @app.route("/category/global", methods=["POST"])
    @roles_required("admin")
    def create_global_category():
        try:
            data = CategorySchema().load(
                request.get_json(silent=True) or {}
            )
        except ValidationError as error:
            return validation_error(error)

        category = Category(
            name=data["name"].strip(),
            user_id=None,
        )

        db.session.add(category)
        db.session.commit()

        return jsonify({
            "id": category.id,
            "name": category.name,
            "user_id": None,
        }), 201

    @app.route("/category/<int:category_id>", methods=["DELETE"])
    @roles_required("admin")
    def delete_category(category_id):
        category = db.session.get(Category, category_id)

        if category is None:
            return not_found("Category not found")

        db.session.delete(category)
        db.session.commit()

        return "", 204

    # ==================== ACCOUNTS ====================

    @app.route("/account/<int:user_id>", methods=["GET"])
    @roles_required("user", "auditor", "admin")
    def get_account(user_id):
        if current_role() == "user" and user_id != get_current_user_id():
            return not_found("Account not found")

        account = Account.query.filter_by(user_id=user_id).first()

        if account is None:
            return not_found("Account not found")

        return jsonify({
            "id": account.id,
            "user_id": account.user_id,
            "balance": str(account.balance),
        }), 200

    @app.route("/account/<int:user_id>/deposit", methods=["POST"])
    @roles_required("user", "admin")
    def deposit_account(user_id):
        if current_role() == "user" and user_id != get_current_user_id():
            return not_found("Account not found")

        account = (
            Account.query
            .filter_by(user_id=user_id)
            .with_for_update()
            .first()
        )

        if account is None:
            return not_found("Account not found")

        try:
            data = DepositSchema().load(
                request.get_json(silent=True) or {}
            )
        except ValidationError as error:
            return validation_error(error)

        account.balance += data["amount"]
        db.session.commit()

        return jsonify({
            "message": "Account topped up successfully",
            "user_id": user_id,
            "balance": str(account.balance),
        }), 200

    # ==================== RECORDS ====================

    @app.route("/record", methods=["POST"])
    @roles_required("user", "admin")
    def create_record():
        try:
            data = RecordSchema().load(
                request.get_json(silent=True) or {}
            )
        except ValidationError as error:
            return validation_error(error)

        if (
            current_role() == "user"
            and data["user_id"] != get_current_user_id()
        ):
            return not_found("User not found")

        user = db.session.get(User, data["user_id"])
        category = db.session.get(Category, data["category_id"])

        if user is None:
            return not_found("User not found")

        if category is None:
            return not_found("Category not found")

        if (
            category.user_id is not None
            and category.user_id != user.id
            and current_role() != "admin"
        ):
            return not_found("Category not found")

        account = (
            Account.query
            .filter_by(user_id=user.id)
            .with_for_update()
            .first()
        )

        if account is None:
            return not_found("Account not found")

        amount = data["amount"]

        if account.balance < amount:
            return jsonify({
                "error": "insufficient_funds",
                "message": "Insufficient account balance",
                "balance": str(account.balance),
                "required": str(amount),
            }), 400

        record = Record(
            user_id=user.id,
            category_id=category.id,
            amount=amount,
        )

        account.balance -= amount
        db.session.add(record)
        db.session.commit()

        return jsonify({
            "id": record.id,
            "user_id": record.user_id,
            "category_id": record.category_id,
            "created_at": record.created_at.isoformat(),
            "amount": str(record.amount),
            "remaining_balance": str(account.balance),
        }), 201

    @app.route("/record/<int:record_id>", methods=["GET"])
    @roles_required("user", "auditor", "admin")
    def get_record(record_id):
        record = db.session.get(Record, record_id)

        if record is None:
            return not_found("Record not found")

        if (
            current_role() == "user"
            and record.user_id != get_current_user_id()
        ):
            return not_found("Record not found")

        return jsonify({
            "id": record.id,
            "user_id": record.user_id,
            "category_id": record.category_id,
            "created_at": record.created_at.isoformat(),
            "amount": str(record.amount),
        }), 200

    @app.route("/record/<int:record_id>", methods=["DELETE"])
    @roles_required("user", "admin")
    def delete_record(record_id):
        record = db.session.get(Record, record_id)

        if record is None:
            return not_found("Record not found")

        if (
            current_role() == "user"
            and record.user_id != get_current_user_id()
        ):
            return not_found("Record not found")

        db.session.delete(record)
        db.session.commit()

        return "", 204

    @app.route("/record", methods=["GET"])
    @roles_required("user", "auditor", "admin")
    def get_records():
        user_id = request.args.get("user_id")
        category_id = request.args.get("category_id")

        if user_id is None and category_id is None:
            return jsonify({
                "error": "invalid_request",
                "message": (
                    "At least one query parameter "
                    "('user_id' or 'category_id') is required for filtration"
                ),
            }), 400

        try:
            user_id = int(user_id) if user_id is not None else None
            category_id = (
                int(category_id) if category_id is not None else None
            )
        except ValueError:
            return jsonify({
                "error": "invalid_request",
                "message": "Invalid query parameter",
            }), 400

        if current_role() == "user":
            own_id = get_current_user_id()

            if user_id is not None and user_id != own_id:
                return not_found("User not found")

            user_id = own_id

        query = Record.query

        if user_id is not None:
            query = query.filter_by(user_id=user_id)

        if category_id is not None:
            query = query.filter_by(category_id=category_id)

        records = query.all()

        return jsonify([
            {
                "id": record.id,
                "user_id": record.user_id,
                "category_id": record.category_id,
                "created_at": record.created_at.isoformat(),
                "amount": str(record.amount),
            }
            for record in records
        ]), 200
