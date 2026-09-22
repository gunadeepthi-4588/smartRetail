"""
Sales Blueprint for SmartRetail REST API
Handles POS sales transactions, atomic inventory deductions, transaction rollbacks,
receipt generation, and historical sales auditing.
"""

from flask import Blueprint, request, jsonify
from app.db import get_db, query_db
from datetime import datetime, timezone
import random
import string

sales_bp = Blueprint("sales", __name__)

def generate_unique_receipt_number(cursor):
    """Generates a collision-resistant receipt number like REC-YYYYMMDD-XXXX."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    for _ in range(10):
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        candidate = f"REC-{date_str}-{random_suffix}"
        cursor.execute("SELECT sale_id FROM sales WHERE receipt_number = %s", (candidate,))
        if not cursor.fetchone():
            return candidate
    # Fallback with timestamp microsecond
    return f"REC-{date_str}-{int(datetime.now(timezone.utc).timestamp() * 1000) % 100000}"

def sanitize_sale(row):
    """Formats sales header row for JSON response."""
    if not row:
        return None
    return {
        "sale_id": int(row["sale_id"]),
        "store_id": int(row["store_id"]),
        "receipt_number": str(row["receipt_number"]),
        "total_amount": float(row["total_amount"]),
        "payment_method": str(row["payment_method"]),
        "sale_date": str(row["sale_date"]) if row.get("sale_date") else None,
        "items_count": int(row.get("items_count", 0)),
        "total_units_sold": int(row.get("total_units_sold", 0))
    }

@sales_bp.route("/sales", methods=["GET"])
def get_sales():
    """
    GET /api/sales
    Returns historical sales transactions with line-item aggregates.
    Supports query parameters: ?payment_method=..., ?receipt=..., ?limit=...
    """
    payment_method = request.args.get("payment_method", "").strip()
    receipt = request.args.get("receipt", "").strip()
    limit = request.args.get("limit", "50").strip()

    sql = """
        SELECT s.sale_id, s.store_id, s.receipt_number, s.total_amount, 
               s.payment_method, s.sale_date,
               COUNT(si.sale_item_id) AS items_count,
               COALESCE(SUM(si.quantity), 0) AS total_units_sold
        FROM sales s
        LEFT JOIN sale_items si ON s.sale_id = si.sale_id
        WHERE 1=1
    """
    params = []

    if payment_method and payment_method != "All":
        sql += " AND s.payment_method = %s"
        params.append(payment_method)

    if receipt:
        sql += " AND s.receipt_number LIKE %s"
        params.append(f"%{receipt}%")

    sql += " GROUP BY s.sale_id ORDER BY s.sale_date DESC"

    try:
        limit_val = min(int(limit), 200)
        sql += f" LIMIT {limit_val};"
    except ValueError:
        sql += " LIMIT 50;"

    try:
        rows = query_db(sql, params)
        sales = [sanitize_sale(r) for r in rows]
        return jsonify({
            "status": "success",
            "count": len(sales),
            "data": sales
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to retrieve sales transactions"}), 500

@sales_bp.route("/sales/<int:sale_id>", methods=["GET"])
def get_sale_detail(sale_id):
    """
    GET /api/sales/<sale_id>
    Retrieves full transaction details with all line items.
    """
    header_sql = """
        SELECT s.sale_id, s.store_id, s.receipt_number, s.total_amount, 
               s.payment_method, s.sale_date
        FROM sales s
        WHERE s.sale_id = %s;
    """
    items_sql = """
        SELECT si.sale_item_id, si.product_id, si.quantity, si.unit_price, si.unit_cost,
               (si.quantity * si.unit_price) AS line_total,
               (si.quantity * (si.unit_price - si.unit_cost)) AS line_profit,
               p.sku, p.name AS product_name, p.category
        FROM sale_items si
        JOIN products p ON si.product_id = p.product_id
        WHERE si.sale_id = %s
        ORDER BY si.sale_item_id ASC;
    """
    try:
        header = query_db(header_sql, (sale_id,), one=True)
        if not header:
            return jsonify({"status": "error", "message": f"Sale transaction with ID {sale_id} not found"}), 404

        raw_items = query_db(items_sql, (sale_id,))
        items = [
            {
                "sale_item_id": int(item["sale_item_id"]),
                "product_id": int(item["product_id"]),
                "sku": str(item["sku"]),
                "product_name": str(item["product_name"]),
                "category": str(item["category"]),
                "quantity": int(item["quantity"]),
                "unit_price": float(item["unit_price"]),
                "unit_cost": float(item["unit_cost"]),
                "line_total": round(float(item["line_total"]), 2),
                "line_profit": round(float(item["line_profit"]), 2)
            }
            for item in raw_items
        ]

        sale_data = sanitize_sale(header)
        sale_data["items_count"] = len(items)
        sale_data["items"] = items

        return jsonify({
            "status": "success",
            "data": sale_data
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to retrieve sale details"}), 500

@sales_bp.route("/sales", methods=["POST"])
def create_sale():
    """
    POST /api/sales
    Executes an atomic point-of-sale checkout:
    1. Validates store and items.
    2. Checks inventory sufficiency for all items.
    3. Inserts sales record.
    4. Inserts sale_items with historical unit cost.
    5. Deducts sold quantities from inventory.
    6. Commits as ONE atomic transaction (Rolls back completely on ANY failure).
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Missing request body"}), 400

    items_data = data.get("items")
    if not items_data or not isinstance(items_data, list) or len(items_data) == 0:
        return jsonify({"status": "error", "message": "Sale must contain at least one item in 'items' array"}), 400

    store_id = int(data.get("store_id", 1))
    payment_method = str(data.get("payment_method", "Cash")).strip()
    if payment_method not in ["Cash", "Card", "UPI"]:
        return jsonify({"status": "error", "message": "Invalid payment_method. Allowed values: Cash, Card, UPI"}), 400

    db = get_db()
    try:
        with db.cursor() as cursor:
            # 1. Verify store exists
            cursor.execute("SELECT store_id FROM stores WHERE store_id = %s", (store_id,))
            if not cursor.fetchone():
                db.rollback()
                return jsonify({"status": "error", "message": f"Store with ID {store_id} does not exist"}), 400

            validated_items = []
            total_amount = 0.0

            # 2. Validate all products and check inventory
            for item in items_data:
                product_id = item.get("product_id")
                quantity = item.get("quantity")

                if not product_id or quantity is None:
                    db.rollback()
                    return jsonify({"status": "error", "message": "Each item must specify 'product_id' and 'quantity'"}), 400

                try:
                    product_id = int(product_id)
                    quantity = int(quantity)
                except (ValueError, TypeError):
                    db.rollback()
                    return jsonify({"status": "error", "message": "Invalid numeric format for product_id or quantity"}), 400

                if quantity <= 0:
                    db.rollback()
                    return jsonify({"status": "error", "message": "Item quantity must be greater than zero"}), 400

                # Query product details & current stock with lock
                cursor.execute("""
                    SELECT p.product_id, p.name, p.sku, p.cost_price, p.selling_price, 
                           i.current_stock
                    FROM products p
                    JOIN inventory i ON p.product_id = i.product_id
                    WHERE p.product_id = %s;
                """, (product_id,))
                prod_row = cursor.fetchone()

                if not prod_row:
                    db.rollback()
                    return jsonify({"status": "error", "message": f"Product ID {product_id} not found in inventory catalog"}), 404

                available_stock = int(prod_row["current_stock"])
                if available_stock < quantity:
                    db.rollback()
                    return jsonify({
                        "status": "error",
                        "message": f"Insufficient stock for '{prod_row['name']}' (SKU: {prod_row['sku']}). Requested: {quantity}, Available: {available_stock}."
                    }), 400

                unit_price = float(item.get("unit_price", prod_row["selling_price"]))
                unit_cost = float(prod_row["cost_price"])

                if unit_price < 0:
                    db.rollback()
                    return jsonify({"status": "error", "message": "Unit price cannot be negative"}), 400

                line_total = round(quantity * unit_price, 2)
                total_amount += line_total

                validated_items.append({
                    "product_id": product_id,
                    "name": prod_row["name"],
                    "sku": prod_row["sku"],
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "unit_cost": unit_cost,
                    "line_total": line_total,
                    "previous_stock": available_stock,
                    "new_stock": available_stock - quantity
                })

            total_amount = round(total_amount, 2)
            receipt_number = generate_unique_receipt_number(cursor)

            # 3. Create Sales Header Record
            cursor.execute("""
                INSERT INTO sales (store_id, receipt_number, total_amount, payment_method, sale_date)
                VALUES (%s, %s, %s, %s, NOW());
            """, (store_id, receipt_number, total_amount, payment_method))
            new_sale_id = cursor.lastrowid

            # 4. Insert Sale Items & Deduct Inventory
            for v_item in validated_items:
                cursor.execute("""
                    INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, unit_cost)
                    VALUES (%s, %s, %s, %s, %s);
                """, (new_sale_id, v_item["product_id"], v_item["quantity"], v_item["unit_price"], v_item["unit_cost"]))

                cursor.execute("""
                    UPDATE inventory
                    SET current_stock = current_stock - %s
                    WHERE product_id = %s;
                """, (v_item["quantity"], v_item["product_id"]))

            # 5. Commit atomic transaction
            db.commit()

        return jsonify({
            "status": "success",
            "message": "Sale completed successfully and inventory updated atomically",
            "data": {
                "sale_id": new_sale_id,
                "receipt_number": receipt_number,
                "total_amount": total_amount,
                "payment_method": payment_method,
                "items_count": len(validated_items),
                "items": validated_items
            }
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": f"Sale transaction failed and was rolled back: {str(e)}"}), 500
