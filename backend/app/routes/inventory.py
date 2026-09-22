"""
Inventory Blueprint for SmartRetail REST API
Handles real-time inventory tracking, stock adjustments, safety thresholds,
and calculated inventory status (Healthy, Low Stock, Out of Stock, Overstocked).
"""

from flask import Blueprint, request, jsonify
from app.db import query_db, execute_db

inventory_bp = Blueprint("inventory", __name__)

def calculate_inventory_status(current_stock, min_stock, max_stock, safety_stock):
    """
    Computes distinct inventory health classification based on stock thresholds.
    - Out of Stock: stock <= 0
    - Low Stock: 0 < stock < safety_stock (or stock <= min_stock)
    - Overstocked: stock >= max_stock (or stock > safety_stock * 3)
    - Healthy: normal buffer range
    """
    if current_stock <= 0:
        return "Out of Stock"
    if current_stock < safety_stock or current_stock <= min_stock:
        return "Low Stock"
    if current_stock >= max_stock:
        return "Overstocked"
    return "Healthy"

def sanitize_inventory(row):
    """Formats raw inventory query row to clean JSON response with computed status."""
    if not row:
        return None
    current_stock = int(row["current_stock"])
    min_stock = int(row["min_stock_level"])
    max_stock = int(row["max_stock_level"])
    safety_stock = int(row["safety_stock"])
    lead_time = int(row["lead_time_days"])

    status = calculate_inventory_status(current_stock, min_stock, max_stock, safety_stock)

    return {
        "inventory_id": int(row["inventory_id"]),
        "product_id": int(row["product_id"]),
        "sku": str(row["sku"]),
        "product_name": str(row["product_name"]),
        "category": str(row["category"]),
        "cost_price": float(row["cost_price"]),
        "selling_price": float(row["selling_price"]),
        "current_stock": current_stock,
        "min_stock_level": min_stock,
        "max_stock_level": max_stock,
        "safety_stock": safety_stock,
        "lead_time_days": lead_time,
        "status": status,
        "inventory_valuation_cost": round(current_stock * float(row["cost_price"]), 2),
        "inventory_valuation_retail": round(current_stock * float(row["selling_price"]), 2),
        "last_updated": str(row["last_updated"]) if row.get("last_updated") else None
    }

@inventory_bp.route("/inventory", methods=["GET"])
def get_inventory():
    """
    GET /api/inventory
    Returns all inventory records with product details and calculated status.
    Supports query parameters: ?status=..., ?category=..., ?search=...
    """
    status_filter = request.args.get("status", "").strip().lower()
    category = request.args.get("category", "").strip()
    search = request.args.get("search", "").strip()

    sql = """
        SELECT i.inventory_id, i.product_id, i.current_stock, i.min_stock_level,
               i.max_stock_level, i.safety_stock, i.lead_time_days, i.last_updated,
               p.sku, p.name AS product_name, p.category, p.cost_price, p.selling_price
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        WHERE 1=1
    """
    params = []

    if category:
        sql += " AND p.category = %s"
        params.append(category)

    if search:
        sql += " AND (p.name LIKE %s OR p.sku LIKE %s)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")

    sql += " ORDER BY p.product_id ASC;"

    try:
        rows = query_db(sql, params)
        items = [sanitize_inventory(r) for r in rows]

        # Apply status filter on computed status
        if status_filter:
            norm_map = {
                "low": "Low Stock",
                "low stock": "Low Stock",
                "low_stock": "Low Stock",
                "out": "Out of Stock",
                "out_of_stock": "Out of Stock",
                "out of stock": "Out of Stock",
                "over": "Overstocked",
                "overstock": "Overstocked",
                "overstocked": "Overstocked",
                "healthy": "Healthy"
            }
            target_status = norm_map.get(status_filter, status_filter.title())
            items = [item for item in items if item["status"] == target_status]

        # Summary KPIs for inventory header
        total_valuation_cost = sum(item["inventory_valuation_cost"] for item in items)
        low_stock_count = sum(1 for item in items if item["status"] == "Low Stock")
        out_of_stock_count = sum(1 for item in items if item["status"] == "Out of Stock")
        overstocked_count = sum(1 for item in items if item["status"] == "Overstocked")

        return jsonify({
            "status": "success",
            "count": len(items),
            "summary": {
                "total_valuation_cost": round(total_valuation_cost, 2),
                "low_stock_count": low_stock_count,
                "out_of_stock_count": out_of_stock_count,
                "overstocked_count": overstocked_count
            },
            "data": items
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to fetch inventory records"}), 500

@inventory_bp.route("/inventory/<int:product_id>", methods=["GET"])
def get_inventory_by_product(product_id):
    """
    GET /api/inventory/<product_id>
    Retrieves inventory status for a specific product ID.
    """
    sql = """
        SELECT i.inventory_id, i.product_id, i.current_stock, i.min_stock_level,
               i.max_stock_level, i.safety_stock, i.lead_time_days, i.last_updated,
               p.sku, p.name AS product_name, p.category, p.cost_price, p.selling_price
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        WHERE i.product_id = %s;
    """
    try:
        row = query_db(sql, (product_id,), one=True)
        if not row:
            return jsonify({"status": "error", "message": f"Inventory record for product ID {product_id} not found"}), 404

        return jsonify({
            "status": "success",
            "data": sanitize_inventory(row)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to fetch inventory item"}), 500

@inventory_bp.route("/inventory/<int:product_id>", methods=["PUT"])
def update_inventory(product_id):
    """
    PUT /api/inventory/<product_id>
    Updates stock levels, buffer parameters, and lead time for a product.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Missing request body"}), 400

    existing = query_db("SELECT * FROM inventory WHERE product_id = %s", (product_id,), one=True)
    if not existing:
        return jsonify({"status": "error", "message": f"Inventory record for product ID {product_id} not found"}), 404

    current_stock = data.get("current_stock", existing["current_stock"])
    min_stock = data.get("min_stock_level", existing["min_stock_level"])
    max_stock = data.get("max_stock_level", existing["max_stock_level"])
    safety_stock = data.get("safety_stock", existing["safety_stock"])
    lead_time = data.get("lead_time_days", existing["lead_time_days"])

    try:
        current_stock = int(current_stock)
        min_stock = int(min_stock)
        max_stock = int(max_stock)
        safety_stock = int(safety_stock)
        lead_time = int(lead_time)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "All inventory parameters must be valid integers"}), 400

    if current_stock < 0 or min_stock < 0 or max_stock < 0 or safety_stock < 0 or lead_time < 0:
        return jsonify({"status": "error", "message": "Inventory parameters cannot be negative"}), 400

    if min_stock > max_stock:
        return jsonify({"status": "error", "message": "min_stock_level cannot be greater than max_stock_level"}), 400

    execute_db("""
        UPDATE inventory 
        SET current_stock = %s, min_stock_level = %s, max_stock_level = %s,
            safety_stock = %s, lead_time_days = %s
        WHERE product_id = %s;
    """, (current_stock, min_stock, max_stock, safety_stock, lead_time, product_id))

    # Fetch updated record
    sql = """
        SELECT i.inventory_id, i.product_id, i.current_stock, i.min_stock_level,
               i.max_stock_level, i.safety_stock, i.lead_time_days, i.last_updated,
               p.sku, p.name AS product_name, p.category, p.cost_price, p.selling_price
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        WHERE i.product_id = %s;
    """
    updated = query_db(sql, (product_id,), one=True)

    return jsonify({
        "status": "success",
        "message": "Inventory updated successfully",
        "data": sanitize_inventory(updated)
    }), 200
