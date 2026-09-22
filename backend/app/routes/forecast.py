from flask import Blueprint, jsonify, request
from app.services.forecast_service import (
    generate_and_save_forecast,
    get_stored_forecasts,
    get_product_forecast_and_history,
    update_actual_demand_if_available
)

forecast_bp = Blueprint("forecast", __name__)

@forecast_bp.route("/forecast", methods=["POST"])
def create_forecast():
    """
    POST /api/forecast
    Generates a new demand forecast for a product and persists it to the database.
    
    Request JSON:
    {
        "product_id": 1,
        "horizon_days": 7  (or 30)
    }
    """
    try:
        data = request.get_json() or {}
        product_id = data.get("product_id")
        horizon_days = data.get("horizon_days", 7)

        if not product_id:
            return jsonify({
                "status": "error",
                "message": "product_id is required."
            }), 400

        try:
            product_id = int(product_id)
            horizon_days = int(horizon_days)
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": "product_id and horizon_days must be integers."
            }), 400

        if horizon_days not in [7, 30]:
            return jsonify({
                "status": "error",
                "message": "horizon_days must be either 7 or 30."
            }), 400

        result = generate_and_save_forecast(product_id=product_id, horizon_days=horizon_days)

        return jsonify({
            "status": "success",
            "message": f"Successfully generated and stored {horizon_days}-day forecast for product {product_id}.",
            "data": result
        }), 201

    except ValueError as ve:
        return jsonify({
            "status": "error",
            "message": str(ve)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to generate forecast: {str(e)}"
        }), 500


@forecast_bp.route("/forecast", methods=["GET"])
def get_forecasts():
    """
    GET /api/forecast
    Retrieves stored forecast records from MySQL.
    Optional query params: product_id, horizon_days, limit
    """
    try:
        product_id = request.args.get("product_id", type=int)
        horizon_days = request.args.get("horizon_days", type=int)
        limit = request.args.get("limit", 100, type=int)

        forecasts = get_stored_forecasts(product_id=product_id, horizon_days=horizon_days, limit=limit)

        return jsonify({
            "status": "success",
            "count": len(forecasts),
            "data": forecasts
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve forecasts: {str(e)}"
        }), 500


@forecast_bp.route("/forecast/<int:product_id>", methods=["GET"])
def get_product_forecast(product_id):
    """
    GET /api/forecast/<product_id>
    Retrieves the latest forecast for a product along with recent historical sales for chart rendering.
    """
    try:
        horizon_days = request.args.get("horizon_days", 7, type=int)
        if horizon_days not in [7, 30]:
            horizon_days = 7

        data = get_product_forecast_and_history(product_id=product_id, horizon_days=horizon_days)

        return jsonify({
            "status": "success",
            "data": data
        }), 200

    except ValueError as ve:
        return jsonify({
            "status": "error",
            "message": str(ve)
        }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve product forecast: {str(e)}"
        }), 500


@forecast_bp.route("/forecast/update-actuals", methods=["POST"])
def update_actuals():
    """
    POST /api/forecast/update-actuals
    Updates actual_demand in stored forecasts where target_date has passed.
    """
    try:
        updated_count = update_actual_demand_if_available()
        return jsonify({
            "status": "success",
            "message": f"Updated actual demand for {updated_count} forecast records.",
            "updated_count": updated_count
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to update actual demand: {str(e)}"
        }), 500
