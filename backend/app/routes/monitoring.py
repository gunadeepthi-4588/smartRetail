"""
Forecast Monitoring & Model Performance Routes
Exposes endpoints to compare predicted demand against actual sales over time.
"""

from flask import Blueprint, jsonify, request
from app.services.monitoring_service import (
    get_forecast_monitoring_data,
    get_monitoring_summary,
    reconcile_actual_demand
)

monitoring_bp = Blueprint("monitoring", __name__)

@monitoring_bp.route("/monitoring/forecast", methods=["GET"])
def get_monitoring_forecast_route():
    """
    GET /api/monitoring/forecast
    Query params:
      - product_id (optional int)
      - days (optional int: 7, 30, 90)
      - model_name (optional str)
    """
    try:
        product_id = request.args.get("product_id")
        days = request.args.get("days", 30)
        model_name = request.args.get("model_name")

        if product_id:
            try:
                product_id = int(product_id)
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid product_id parameter"}), 400

        try:
            days = int(days)
        except ValueError:
            days = 30

        result = get_forecast_monitoring_data(product_id=product_id, days=days, model_name=model_name)
        
        response = {
            "status": "success",
            "product_id": result["product_id"],
            "days": result["days"],
            "model_name": result["model_name"],
            "sample_count": result["sample_count"],
            "data": result["data"]
        }
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to retrieve forecast monitoring data: {str(e)}"}), 500


@monitoring_bp.route("/monitoring/summary", methods=["GET"])
def get_monitoring_summary_route():
    """
    GET /api/monitoring/summary
    Query params:
      - product_id (optional int)
      - days (optional int: 7, 30, 90)
      - model_name (optional str)
    """
    try:
        product_id = request.args.get("product_id")
        days = request.args.get("days", 30)
        model_name = request.args.get("model_name")

        if product_id:
            try:
                product_id = int(product_id)
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid product_id parameter"}), 400

        try:
            days = int(days)
        except ValueError:
            days = 30

        summary = get_monitoring_summary(product_id=product_id, days=days, model_name=model_name)

        response = {
            "status": "success",
            **summary
        }
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to calculate monitoring summary: {str(e)}"}), 500


@monitoring_bp.route("/monitoring/reconcile", methods=["POST"])
def reconcile_actuals_route():
    """
    POST /api/monitoring/reconcile
    Trigger synchronization of actual sales into historical forecast records.
    """
    try:
        data = request.get_json(silent=True) or {}
        product_id = data.get("product_id")
        if product_id:
            try:
                product_id = int(product_id)
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid product_id"}), 400

        updated_count = reconcile_actual_demand(product_id=product_id)
        return jsonify({
            "status": "success",
            "message": f"Successfully reconciled actual sales for {updated_count} forecast records.",
            "records_updated": updated_count
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to reconcile actuals: {str(e)}"}), 500
