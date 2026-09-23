"""
SmartRetail Authentication Routes
Provides secure local login validation, password hash checking, and user profile metadata.
Never returns passwords or password hashes.
"""

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash
from app.db import query_db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/auth/login", methods=["POST"])
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/auth/login or /api/login
    Payload: { "email": "owner@smartretail.com", "password": "SmartRetail@123" }
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Missing request body"}), 400

    identifier = str(data.get("email") or data.get("username") or "").strip()
    password = str(data.get("password") or "")

    if not identifier or not password:
        return jsonify({
            "status": "error",
            "message": "Both email/username and password are required"
        }), 400

    # Query user and associated store details
    sql = """
        SELECT 
            u.user_id,
            u.store_id,
            u.username,
            u.password_hash,
            u.email,
            s.name AS store_name,
            s.owner_name,
            s.currency,
            s.currency_symbol
        FROM users u
        JOIN stores s ON u.store_id = s.store_id
        WHERE LOWER(u.email) = LOWER(%s) OR LOWER(u.username) = LOWER(%s)
        LIMIT 1;
    """
    user_row = query_db(sql, (identifier, identifier), one=True)

    if not user_row or not check_password_hash(user_row["password_hash"], password):
        return jsonify({
            "status": "error",
            "message": "Invalid email or password"
        }), 401

    # Sanitized response object — never exposes password or hash
    user_payload = {
        "user_id": int(user_row["user_id"]),
        "store_id": int(user_row["store_id"]),
        "username": user_row["username"],
        "name": user_row["owner_name"],
        "email": user_row["email"],
        "role": "Store Owner",
        "store_name": user_row["store_name"],
        "currency": user_row["currency"],
        "currency_symbol": user_row["currency_symbol"]
    }

    return jsonify({
        "status": "success",
        "message": "Login successful",
        "user": user_payload
    }), 200


@auth_bp.route("/auth/me", methods=["GET"])
def get_current_user():
    """
    GET /api/auth/me
    Retrieves current store owner context for session validation.
    """
    user_id = request.args.get("user_id", 1, type=int)
    sql = """
        SELECT 
            u.user_id,
            u.store_id,
            u.username,
            u.email,
            s.name AS store_name,
            s.owner_name,
            s.currency,
            s.currency_symbol
        FROM users u
        JOIN stores s ON u.store_id = s.store_id
        WHERE u.user_id = %s
        LIMIT 1;
    """
    user_row = query_db(sql, (user_id,), one=True)
    if not user_row:
        return jsonify({"status": "error", "message": "User not found"}), 404

    return jsonify({
        "status": "success",
        "user": {
            "user_id": int(user_row["user_id"]),
            "store_id": int(user_row["store_id"]),
            "username": user_row["username"],
            "name": user_row["owner_name"],
            "email": user_row["email"],
            "role": "Store Owner",
            "store_name": user_row["store_name"],
            "currency": user_row["currency"],
            "currency_symbol": user_row["currency_symbol"]
        }
    }), 200


@auth_bp.route("/auth/logout", methods=["POST"])
@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    POST /api/auth/logout
    """
    return jsonify({
        "status": "success",
        "message": "Logged out successfully"
    }), 200
