from flask import Flask, jsonify
from flask_cors import CORS
from config import config_by_name
import os

def create_app(config_name=None):
    """
    Application factory for SmartRetail Flask backend.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    # Enable Cross-Origin Resource Sharing for React frontend communication
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from app.routes.health import health_bp
    app.register_blueprint(health_bp, url_prefix="/api")

    # Global 404 error handler
    @app.errorhandler(404)
    def resource_not_found(e):
        return jsonify({"error": "Resource not found", "status": 404}), 404

    # Global 500 error handler
    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({"error": "Internal server error", "status": 500}), 500

    return app
