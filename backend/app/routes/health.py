from flask import Blueprint, jsonify
from app.db import check_db_health
from datetime import datetime, timezone

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Standard application health check endpoint.
    Verifies that the Flask web server is active and responding.
    """
    return jsonify({
        "status": "online",
        "service": "SmartRetail Backend API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }), 200

@health_bp.route("/health/db", methods=["GET"])
def db_health_check():
    """
    Database connectivity check endpoint.
    Verifies that Flask can establish a safe connection with MySQL.
    Never exposes passwords, internal hosts, or sensitive credentials.
    """
    db_result = check_db_health()
    
    response_payload = {
        "status": "ok" if db_result.get("status") == "connected" else "error",
        "database": db_result.get("status"),
        "database_name": db_result.get("database_name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    if db_result.get("status") == "connected":
        response_payload["tables_count"] = db_result.get("tables_found", 0)
        return jsonify(response_payload), 200
    else:
        response_payload["message"] = "Unable to connect to database. Verify credentials in backend/.env"
        return jsonify(response_payload), 503
