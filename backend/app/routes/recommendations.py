from flask import Blueprint, jsonify, request
from app.services.inventory_intelligence_service import (
    get_all_inventory_intelligence,
    calculate_product_inventory_intelligence,
    persist_reorder_recommendation
)

recommendations_bp = Blueprint("recommendations", __name__)

@recommendations_bp.route("/inventory/intelligence", methods=["GET"])
def get_inventory_intelligence():
    """
    GET /api/inventory/intelligence?days=7
    Returns stockout risk, overstock risk, lead-time demand, and reorder recommendations for all products.
    """
    try:
        days = request.args.get("days", 7, type=int)
        if days not in [7, 30]:
            return jsonify({
                "status": "error",
                "message": "days must be either 7 or 30."
            }), 400

        data = get_all_inventory_intelligence(horizon_days=days)

        return jsonify({
            "status": "success",
            "planning_horizon_days": days,
            "count": len(data),
            "data": data
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to compute inventory intelligence: {str(e)}"
        }), 500


@recommendations_bp.route("/inventory/intelligence/<int:product_id>", methods=["GET"])
def get_single_inventory_intelligence(product_id):
    """
    GET /api/inventory/intelligence/<product_id>?days=7
    Returns inventory intelligence and reorder recommendation for a single product.
    """
    try:
        days = request.args.get("days", 7, type=int)
        if days not in [7, 30]:
            return jsonify({
                "status": "error",
                "message": "days must be either 7 or 30."
            }), 400

        intel = calculate_product_inventory_intelligence(product_id, horizon_days=days)
        persist_reorder_recommendation(intel)

        return jsonify({
            "status": "success",
            "data": intel
        }), 200

    except ValueError as ve:
        return jsonify({
            "status": "error",
            "message": str(ve)
        }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to compute intelligence for product {product_id}: {str(e)}"
        }), 500


@recommendations_bp.route("/recommendations", methods=["GET"])
def get_recommendations():
    """
    GET /api/recommendations?days=7&status=REORDER
    Returns filtered reorder recommendations list for the store owner.
    """
    try:
        days = request.args.get("days", 7, type=int)
        if days not in [7, 30]:
            days = 7

        status_filter = request.args.get("status") # e.g. REORDER or NO_REORDER

        data = get_all_inventory_intelligence(horizon_days=days)

        if status_filter:
            data = [d for d in data if d["recommendation_status"].upper() == status_filter.upper()]

        return jsonify({
            "status": "success",
            "planning_horizon_days": days,
            "count": len(data),
            "data": data
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve recommendations: {str(e)}"
        }), 500


@recommendations_bp.route("/recommendations/<int:product_id>", methods=["GET"])
def get_single_recommendation(product_id):
    """
    GET /api/recommendations/<product_id>?days=7
    """
    return get_single_inventory_intelligence(product_id)
