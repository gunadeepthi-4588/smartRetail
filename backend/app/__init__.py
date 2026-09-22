from flask import Flask, jsonify
from flask_cors import CORS
from config import config_by_name
from app.db import init_app as init_db_app
import os

def create_app(config_name=None):
    """
    Application factory for SmartRetail Flask backend.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    # Initialize Database teardown handling
    init_db_app(app)

    # Enable Cross-Origin Resource Sharing for React frontend communication
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from app.routes.health import health_bp
    from app.routes.products import products_bp
    from app.routes.inventory import inventory_bp
    from app.routes.sales import sales_bp
    from app.routes.analytics import analytics_bp
    from app.routes.forecast import forecast_bp
    from app.routes.recommendations import recommendations_bp
    from app.routes.monitoring import monitoring_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(products_bp, url_prefix="/api")
    app.register_blueprint(inventory_bp, url_prefix="/api")
    app.register_blueprint(sales_bp, url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api")
    app.register_blueprint(forecast_bp, url_prefix="/api")
    app.register_blueprint(recommendations_bp, url_prefix="/api")
    app.register_blueprint(monitoring_bp, url_prefix="/api")

    # Global 404 error handler
    @app.errorhandler(404)
    def resource_not_found(e):
        return jsonify({"status": "error", "message": "Resource not found"}), 404

    # Global 500 error handler
    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({"status": "error", "message": "Internal server error"}), 500

    return app
