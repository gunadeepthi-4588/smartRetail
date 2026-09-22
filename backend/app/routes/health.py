from flask import Blueprint, jsonify
import datetime

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint to verify backend status and timestamp.
    """
    return jsonify({
        "status": "online",
        "service": "SmartRetail Backend API",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0"
    }), 200
