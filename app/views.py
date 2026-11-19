
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from flask import jsonify, request

from app import storage


def register_routes(app):

    # Перевірка працездатності застосунку
    @app.route("/healthz/live", methods=["GET"])
    def liveness_check():
        return jsonify({
            "status": "alive",
            "timestamp": datetime.now(UTC).isoformat()
        }), 200

    # Перевірка готовності застосунку
    @app.route("/healthz/ready", methods=["GET"])
    def readiness_check():
        return jsonify({
            "status": "ready",
            "database": "not_connected_yet",
            "timestamp": datetime.now(UTC).isoformat()
        }), 200

    # ==================== USER ====================

    # Отримання всіх користувачів
    @app.route("/users", methods=["GET"])
    def get_users():
        return jsonify(list(storage.users.values())), 200

    # Отримання користувача за ID
    @app.route("/user/<int:user_id>", methods=["GET"])
    def get_user(user_id):
        user = storage.users.get(user_id)

        if user is None:
            return jsonify({"error": "User not found"}), 404

        return jsonify(user), 200

    # Створення користувача
    @app.route("/user", methods=["POST"])
    def create_user():
        data = request.get_json(silent=True)

        if not isinstance(data, dict) or not isinstance(data.get("name"), str) or not data["name"].strip():
            return jsonify({"error": "Name is required"}), 400

        user_id = storage.next_user_id
        storage.next_user_id += 1

        user = {
            "id": user_id,
            "name": data["name"].strip()
        }

        storage.users[user_id] = user

        return jsonify(user), 201

    # Видалення користувача
    @app.route("/user/<int:user_id>", methods=["DELETE"])
    def delete_user(user_id):
        if user_id not in storage.users:
            return jsonify({"error": "User not found"}), 404

        del storage.users[user_id]

        return "", 204

    # ==================== CATEGORY ====================

    # Отримання всіх категорій
    @app.route("/category", methods=["GET"])
    def get_categories():
        return jsonify(list(storage.categories.values())), 200

    # Створення категорії
    @app.route("/category", methods=["POST"])
    def create_category():
        data = request.get_json(silent=True)

        if not isinstance(data, dict) or not isinstance(data.get("name"), str) or not data["name"].strip():
            return jsonify({"error": "Name is required"}), 400

        category_id = storage.next_category_id
        storage.next_category_id += 1

        category = {
            "id": category_id,
            "name": data["name"].strip()
        }

        storage.categories[category_id] = category

        return jsonify(category), 201

    # Видалення категорії
    @app.route("/category/<int:category_id>", methods=["DELETE"])
    def delete_category(category_id):
        if category_id not in storage.categories:
            return jsonify({"error": "Category not found"}), 404

        del storage.categories[category_id]

        return "", 204

    # ==================== RECORD ====================

    # Створення запису про витрати
    @app.route("/record", methods=["POST"])
    def create_record():
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Invalid JSON"}), 400

        try:
            user_id = int(data["user_id"])
            category_id = int(data["category_id"])
            amount = Decimal(str(data["amount"]))
        except (KeyError, ValueError, TypeError, InvalidOperation):
            return jsonify({"error": "Invalid record data"}), 400

        if user_id not in storage.users:
            return jsonify({"error": "User not found"}), 404

        if category_id not in storage.categories:
            return jsonify({"error": "Category not found"}), 404

        if not amount.is_finite() or amount <= 0:
            return jsonify({"error": "Amount must be a positive number"}), 400

        record_id = storage.next_record_id
        storage.next_record_id += 1

        record = {
            "id": record_id,
            "user_id": user_id,
            "category_id": category_id,
            "created_at": datetime.now(UTC).isoformat(),
            "amount": str(amount)
        }

        storage.records[record_id] = record

        return jsonify(record), 201

    # Отримання запису за ID
    @app.route("/record/<int:record_id>", methods=["GET"])
    def get_record(record_id):
        record = storage.records.get(record_id)

        if record is None:
            return jsonify({"error": "Record not found"}), 404

        return jsonify(record), 200

    # Видалення запису
    @app.route("/record/<int:record_id>", methods=["DELETE"])
    def delete_record(record_id):
        if record_id not in storage.records:
            return jsonify({"error": "Record not found"}), 404

        del storage.records[record_id]

        return "", 204

    # Фільтрація записів за користувачем та категорією
    @app.route("/record", methods=["GET"])
    def get_records():
        user_id = request.args.get("user_id")
        category_id = request.args.get("category_id")

        if user_id is None and category_id is None:
            return jsonify({
                "error": "invalid_request",
                "message": "At least one query parameter ('user_id' or 'category_id') is required for filtration"
            }), 400

        try:
            user_id = int(user_id) if user_id is not None else None
            category_id = int(category_id) if category_id is not None else None
        except ValueError:
            return jsonify({"error": "Invalid query parameter"}), 400

        filtered_records = []

        for record in storage.records.values():
            if user_id is not None and record["user_id"] != user_id:
                continue

            if category_id is not None and record["category_id"] != category_id:
                continue

            filtered_records.append(record)

        return jsonify(filtered_records), 200
