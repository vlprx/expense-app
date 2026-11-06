from datetime import UTC, datetime

from flask import jsonify


def register_routes(app):

    @app.route("/healthz/live", methods=["GET"])
    def liveness_check():
        return jsonify({
            "status": "alive",
            "timestamp": datetime.now(UTC).isoformat()
        }), 200

    @app.route("/healthz/ready", methods=["GET"])
    def readiness_check():
        return jsonify({
            "status": "ready",
            "database": "not_connected_yet",
            "timestamp": datetime.now(UTC).isoformat()
        }), 200