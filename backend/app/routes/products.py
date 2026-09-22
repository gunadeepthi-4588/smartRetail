"""
Products Blueprint for SmartRetail REST API
Handles CRUD operations for the product catalog with strict validation,
SKU uniqueness, referential integrity protection, and inventory synchronization.
"""

from flask import Blueprint, request, jsonify
from app.db import get_db, query_db, execute_db
import pymysql

products_bp = Blueprint("products", __name__)

def sanitize_product(row):
    """Formats database row to JSON-safe dictionary with numeric conversions."""
    if not row:
        return None
    return {
        "product_id": int(row["product_id"]),
        "store_id": int(row["store_id"]),
        "supplier_id": int(row["supplier_id"]) if row.get("supplier_id") is not None else None,
        "supplier_name": row.get("supplier_name"),
        "sku": str(row["sku"]),
        "name": str(row["name"]),
        "category": str(row["category"]),
        "cost_price": float(row["cost_price"]),
        "selling_price": float(row["selling_price"]),
        "current_stock": int(row["current_stock"]) if row.get("current_stock") is not None else 0,
        "safety_stock": int(row["safety_stock"]) if row.get("safety_stock") is not None else 0,
        "created_at": str(row["created_at"]) if row.get("created_at") else None
    }

@products_bp.route("/products", methods=["GET"])
def get_products():
    """
    GET /api/products
    Retrieves all products with current stock and supplier info.
    Supports query parameters: ?category=..., ?search=..., ?supplier_id=...
    """
    category = request.args.get("category", "").strip()
    search = request.args.get("search", "").strip()
    supplier_id = request.args.get("supplier_id", "").strip()

    sql = """
        SELECT p.product_id, p.store_id, p.supplier_id, p.sku, p.name, 
               p.category, p.cost_price, p.selling_price, p.created_at,
               s.name AS supplier_name,
               COALESCE(i.current_stock, 0) AS current_stock,
               COALESCE(i.safety_stock, 0) AS safety_stock
        FROM products p
        LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
        LEFT JOIN inventory i ON p.product_id = i.product_id
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

    if supplier_id:
        try:
            params.append(int(supplier_id))
            sql += " AND p.supplier_id = %s"
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid supplier_id parameter"}), 400

    sql += " ORDER BY p.product_id ASC;"

    try:
        rows = query_db(sql, params)
        products = [sanitize_product(r) for r in rows]
        return jsonify({
            "status": "success",
            "count": len(products),
            "data": products
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to fetch products"}), 500

@products_bp.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """
    GET /api/products/<product_id>
    Retrieves a single product by ID.
    """
    sql = """
        SELECT p.product_id, p.store_id, p.supplier_id, p.sku, p.name, 
               p.category, p.cost_price, p.selling_price, p.created_at,
               s.name AS supplier_name,
               COALESCE(i.current_stock, 0) AS current_stock,
               COALESCE(i.min_stock_level, 0) AS min_stock_level,
               COALESCE(i.max_stock_level, 0) AS max_stock_level,
               COALESCE(i.safety_stock, 0) AS safety_stock,
               COALESCE(i.lead_time_days, 3) AS lead_time_days
        FROM products p
        LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
        LEFT JOIN inventory i ON p.product_id = i.product_id
        WHERE p.product_id = %s;
    """
    try:
        row = query_db(sql, (product_id,), one=True)
        if not row:
            return jsonify({"status": "error", "message": f"Product with ID {product_id} not found"}), 404

        data = sanitize_product(row)
        data["min_stock_level"] = int(row["min_stock_level"])
        data["max_stock_level"] = int(row["max_stock_level"])
        data["lead_time_days"] = int(row["lead_time_days"])
        
        return jsonify({
            "status": "success",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to fetch product details"}), 500

@products_bp.route("/products", methods=["POST"])
def create_product():
    """
    POST /api/products
    Creates a new product and initializes its inventory entry.
    Validates required fields, numeric constraints, and SKU uniqueness.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Missing request body"}), 400

    # Required field validation
    sku = str(data.get("sku", "")).strip()
    name = str(data.get("name", "")).strip()
    category = str(data.get("category", "")).strip()
    cost_price = data.get("cost_price")
    selling_price = data.get("selling_price")
    store_id = data.get("store_id", 1)
    supplier_id = data.get("supplier_id")

    if not sku:
        return jsonify({"status": "error", "message": "Field 'sku' is required"}), 400
    if not name:
        return jsonify({"status": "error", "message": "Field 'name' is required"}), 400
    if not category:
        return jsonify({"status": "error", "message": "Field 'category' is required"}), 400
    if cost_price is None or selling_price is None:
        return jsonify({"status": "error", "message": "Fields 'cost_price' and 'selling_price' are required"}), 400

    # Numeric validations
    try:
        cost_price = float(cost_price)
        selling_price = float(selling_price)
        store_id = int(store_id)
        supplier_id = int(supplier_id) if supplier_id is not None else None
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid numeric format for prices or IDs"}), 400

    if cost_price < 0 or selling_price < 0:
        return jsonify({"status": "error", "message": "Prices cannot be negative"}), 400

    # Verify store exists
    store = query_db("SELECT store_id FROM stores WHERE store_id = %s", (store_id,), one=True)
    if not store:
        return jsonify({"status": "error", "message": f"Store with ID {store_id} does not exist"}), 400

    # Verify supplier exists if specified
    if supplier_id:
        supplier = query_db("SELECT supplier_id FROM suppliers WHERE supplier_id = %s", (supplier_id,), one=True)
        if not supplier:
            return jsonify({"status": "error", "message": f"Supplier with ID {supplier_id} does not exist"}), 400

    # Verify SKU uniqueness
    existing_sku = query_db("SELECT product_id FROM products WHERE sku = %s", (sku,), one=True)
    if existing_sku:
        return jsonify({"status": "error", "message": f"A product with SKU '{sku}' already exists"}), 409

    # Optional initial inventory parameters
    current_stock = int(data.get("current_stock", 0))
    min_stock_level = int(data.get("min_stock_level", 10))
    max_stock_level = int(data.get("max_stock_level", 200))
    safety_stock = int(data.get("safety_stock", 20))
    lead_time_days = int(data.get("lead_time_days", 3))

    if current_stock < 0 or safety_stock < 0:
        return jsonify({"status": "error", "message": "Stock values cannot be negative"}), 400

    # Atomic creation of product + inventory
    db = get_db()
    try:
        with db.cursor() as cursor:
            # 1. Insert product
            cursor.execute("""
                INSERT INTO products (store_id, supplier_id, sku, name, category, cost_price, selling_price)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (store_id, supplier_id, sku, name, category, cost_price, selling_price))
            new_product_id = cursor.lastrowid

            # 2. Insert initial inventory record
            cursor.execute("""
                INSERT INTO inventory (product_id, current_stock, min_stock_level, max_stock_level, safety_stock, lead_time_days)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (new_product_id, current_stock, min_stock_level, max_stock_level, safety_stock, lead_time_days))
            
            db.commit()

        # Fetch created product
        created = query_db("""
            SELECT p.product_id, p.store_id, p.supplier_id, p.sku, p.name, 
                   p.category, p.cost_price, p.selling_price, p.created_at,
                   s.name AS supplier_name,
                   i.current_stock, i.safety_stock
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
            LEFT JOIN inventory i ON p.product_id = i.product_id
            WHERE p.product_id = %s;
        """, (new_product_id,), one=True)

        return jsonify({
            "status": "success",
            "message": "Product created successfully",
            "data": sanitize_product(created)
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": "Failed to create product"}), 500

@products_bp.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    """
    PUT /api/products/<product_id>
    Updates existing product details.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Missing request body"}), 400

    # Verify product exists
    existing = query_db("SELECT * FROM products WHERE product_id = %s", (product_id,), one=True)
    if not existing:
        return jsonify({"status": "error", "message": f"Product with ID {product_id} not found"}), 404

    # Extract update fields
    name = data.get("name", existing["name"]).strip()
    category = data.get("category", existing["category"]).strip()
    sku = data.get("sku", existing["sku"]).strip()
    cost_price = data.get("cost_price", existing["cost_price"])
    selling_price = data.get("selling_price", existing["selling_price"])
    supplier_id = data.get("supplier_id", existing["supplier_id"])

    try:
        cost_price = float(cost_price)
        selling_price = float(selling_price)
        supplier_id = int(supplier_id) if supplier_id is not None else None
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid numeric format"}), 400

    if cost_price < 0 or selling_price < 0:
        return jsonify({"status": "error", "message": "Prices cannot be negative"}), 400

    # Verify SKU uniqueness if changed
    if sku != existing["sku"]:
        sku_clash = query_db("SELECT product_id FROM products WHERE sku = %s AND product_id != %s", (sku, product_id), one=True)
        if sku_clash:
            return jsonify({"status": "error", "message": f"A product with SKU '{sku}' already exists"}), 409

    # Verify supplier if provided
    if supplier_id:
        supplier = query_db("SELECT supplier_id FROM suppliers WHERE supplier_id = %s", (supplier_id,), one=True)
        if not supplier:
            return jsonify({"status": "error", "message": f"Supplier with ID {supplier_id} does not exist"}), 400

    execute_db("""
        UPDATE products 
        SET name = %s, category = %s, sku = %s, cost_price = %s, selling_price = %s, supplier_id = %s
        WHERE product_id = %s;
    """, (name, category, sku, cost_price, selling_price, supplier_id, product_id))

    updated = query_db("""
        SELECT p.product_id, p.store_id, p.supplier_id, p.sku, p.name, 
               p.category, p.cost_price, p.selling_price, p.created_at,
               s.name AS supplier_name,
               COALESCE(i.current_stock, 0) AS current_stock,
               COALESCE(i.safety_stock, 0) AS safety_stock
        FROM products p
        LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
        LEFT JOIN inventory i ON p.product_id = i.product_id
        WHERE p.product_id = %s;
    """, (product_id,), one=True)

    return jsonify({
        "status": "success",
        "message": "Product updated successfully",
        "data": sanitize_product(updated)
    }), 200

@products_bp.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """
    DELETE /api/products/<product_id>
    Safely deletes a product only if no dependent sales records exist.
    """
    existing = query_db("SELECT * FROM products WHERE product_id = %s", (product_id,), one=True)
    if not existing:
        return jsonify({"status": "error", "message": f"Product with ID {product_id} not found"}), 404

    # Check for dependent sales records
    sales_count_row = query_db("SELECT COUNT(*) AS cnt FROM sale_items WHERE product_id = %s", (product_id,), one=True)
    sales_count = sales_count_row["cnt"] if sales_count_row else 0

    if sales_count > 0:
        return jsonify({
            "status": "error",
            "message": f"Cannot delete '{existing['name']}' (SKU: {existing['sku']}) because it has {sales_count} associated sales transaction records. Deleting it would compromise sales history and audit trails."
        }), 409

    # Check for forecasts/recommendations
    execute_db("DELETE FROM forecasts WHERE product_id = %s;", (product_id,))
    execute_db("DELETE FROM reorder_recommendations WHERE product_id = %s;", (product_id,))
    execute_db("DELETE FROM inventory WHERE product_id = %s;", (product_id,))
    execute_db("DELETE FROM products WHERE product_id = %s;", (product_id,))

    return jsonify({
        "status": "success",
        "message": f"Product '{existing['name']}' (ID: {product_id}) and its inventory records were successfully deleted"
    }), 200
