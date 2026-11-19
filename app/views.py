
from datetime import UTC, datetime
from decimal import Decimal

from flask import jsonify, request
from marshmallow import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import Account, Category, Record, User
from app.schemas import (
    CategorySchema,
    DepositSchema,
    RecordSchema,
    UserSchema,
)


def validation_error(error):
    return jsonify({
        "error": "validation_error",
        "messages": error.messages,
    }), 400


def register_routes(app):

    # Перевірка працездатності застосунку
    @app.route("/healthz/live", methods=["GET"])
    def liveness_check():
        return jsonify({
            "status": "alive",
            "timestamp": datetime.now(UTC).isoformat(),
        }), 200

    # Перевірка готовності бази даних
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

    # ==================== USER ====================

    @app.route("/users", methods=["GET"])
    def get_users():
        users = User.query.all()
        return jsonify([
            {"id": user.id, "name": user.name}
            for user in users
        ]), 200

    @app.route("/user/<int:user_id>", methods=["GET"])
    def get_user(user_id):
        user = db.session.get(User, user_id)

        if user is None:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "id": user.id,
            "name": user.name,
            "account": {
                "id": user.account.id,
                "balance": str(user.account.balance),
            } if user.account else None,
        }), 200

    @app.route("/user", methods=["POST"])
    def create_user():
        try:
            data = UserSchema().load(request.get_json(silent=True) or {})
        except ValidationError as error:
            return validation_error(error)

        user = User(name=data["name"].strip())
        db.session.add(user)
        db.session.flush()

        account = Account(
            user_id=user.id,
            balance=Decimal("0.00"),
        )

        db.session.add(account)
        db.session.commit()

        return jsonify({
            "id": user.id,
            "name": user.name,
            "account": {
                "id": account.id,
                "balance": str(account.balance),
            },
        }), 201

    @app.route("/user/<int:user_id>", methods=["DELETE"])
    def delete_user(user_id):
        user = db.session.get(User, user_id)

        if user is None:
            return jsonify({"error": "User not found"}), 404

        db.session.delete(user)
        db.session.commit()

        return "", 204

    # ==================== CATEGORY ====================

    @app.route("/category", methods=["GET"])
    def get_categories():
        categories = Category.query.all()

        return jsonify([
            {"id": category.id, "name": category.name}
            for category in categories
        ]), 200

    @app.route("/category", methods=["POST"])
    def create_category():
        try:
            data = CategorySchema().load(request.get_json(silent=True) or {})
        except ValidationError as error:
            return validation_error(error)

        category = Category(name=data["name"].strip())
        db.session.add(category)
        db.session.commit()

        return jsonify({
            "id": category.id,
            "name": category.name,
        }), 201

    @app.route("/category/<int:category_id>", methods=["DELETE"])
    def delete_category(category_id):
        category = db.session.get(Category, category_id)

        if category is None:
            return jsonify({"error": "Category not found"}), 404

        db.session.delete(category)
        db.session.commit()

        return "", 204

    # ==================== ACCOUNT ====================

    @app.route("/account/<int:user_id>", methods=["GET"])
    def get_account(user_id):
        account = Account.query.filter_by(user_id=user_id).first()

        if account is None:
            return jsonify({"error": "Account not found"}), 404

        return jsonify({
            "id": account.id,
            "user_id": account.user_id,
            "balance": str(account.balance),
        }), 200

    @app.route("/account/<int:user_id>/deposit", methods=["POST"])
    def deposit_account(user_id):
        account = (
            Account.query
            .filter_by(user_id=user_id)
            .with_for_update()
            .first()
        )

        if account is None:
            return jsonify({"error": "Account not found"}), 404

        try:
            data = DepositSchema().load(request.get_json(silent=True) or {})
        except ValidationError as error:
            return validation_error(error)

        account.balance += data["amount"]
        db.session.commit()

        return jsonify({
            "message": "Account topped up successfully",
            "user_id": user_id,
            "balance": str(account.balance),
        }), 200

    # ==================== RECORD ====================

    @app.route("/record", methods=["POST"])
    def create_record():
        try:
            data = RecordSchema().load(request.get_json(silent=True) or {})
        except ValidationError as error:
            return validation_error(error)

        user = db.session.get(User, data["user_id"])
        category = db.session.get(Category, data["category_id"])

        if user is None:
            return jsonify({"error": "User not found"}), 404

        if category is None:
            return jsonify({"error": "Category not found"}), 404

        account = (
            Account.query
            .filter_by(user_id=user.id)
            .with_for_update()
            .first()
        )

        if account is None:
            return jsonify({"error": "Account not found"}), 404

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
    def get_record(record_id):
        record = db.session.get(Record, record_id)

        if record is None:
            return jsonify({"error": "Record not found"}), 404

        return jsonify({
            "id": record.id,
            "user_id": record.user_id,
            "category_id": record.category_id,
            "created_at": record.created_at.isoformat(),
            "amount": str(record.amount),
        }), 200

    @app.route("/record/<int:record_id>", methods=["DELETE"])
    def delete_record(record_id):
        record = db.session.get(Record, record_id)

        if record is None:
            return jsonify({"error": "Record not found"}), 404

        db.session.delete(record)
        db.session.commit()

        return "", 204

    @app.route("/record", methods=["GET"])
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
            return jsonify({"error": "Invalid query parameter"}), 400

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
