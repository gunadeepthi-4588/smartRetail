import pytest
from unittest.mock import patch, MagicMock
from app import create_app

@pytest.fixture
def client():
    app = create_app("testing")
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_get_all_products(client):
    """Verifies GET /api/products returns structured product list."""
    mock_data = [
        {
            "product_id": 1,
            "store_id": 1,
            "supplier_id": 1,
            "supplier_name": "Heritage Dairy",
            "sku": "SKU-BEV-001",
            "name": "Masala Chai Tea Bags 250g",
            "category": "Beverages",
            "cost_price": 90.0,
            "selling_price": 135.0,
            "current_stock": 12,
            "safety_stock": 25,
            "created_at": "2026-01-05 10:00:00"
        }
    ]
    with patch("app.routes.products.query_db", return_value=mock_data):
        res = client.get("/api/products")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["count"] == 1
        assert json_data["data"][0]["sku"] == "SKU-BEV-001"

def test_get_product_by_id_found(client):
    """Verifies GET /api/products/<id> returns single product with full inventory fields."""
    mock_row = {
        "product_id": 1,
        "store_id": 1,
        "supplier_id": 1,
        "supplier_name": "Heritage Dairy",
        "sku": "SKU-BEV-001",
        "name": "Masala Chai Tea Bags 250g",
        "category": "Beverages",
        "cost_price": 90.0,
        "selling_price": 135.0,
        "current_stock": 12,
        "min_stock_level": 30,
        "max_stock_level": 150,
        "safety_stock": 25,
        "lead_time_days": 2,
        "created_at": "2026-01-05 10:00:00"
    }
    with patch("app.routes.products.query_db", return_value=mock_row):
        res = client.get("/api/products/1")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["data"]["sku"] == "SKU-BEV-001"
        assert json_data["data"]["lead_time_days"] == 2

def test_get_product_not_found(client):
    """Verifies GET /api/products/<id> returns 404 for nonexistent ID."""
    with patch("app.routes.products.query_db", return_value=None):
        res = client.get("/api/products/99999")
        assert res.status_code == 404
        assert res.get_json()["status"] == "error"

def test_create_product_success(client):
    """Verifies POST /api/products creates product and initial inventory."""
    payload = {
        "sku": "SKU-TEST-001",
        "name": "Organic Green Tea 100g",
        "category": "Beverages",
        "cost_price": 75.0,
        "selling_price": 120.0,
        "store_id": 1,
        "current_stock": 50,
        "safety_stock": 15
    }
    
    mock_store = {"store_id": 1}
    mock_created = {
        "product_id": 21,
        "store_id": 1,
        "supplier_id": None,
        "supplier_name": None,
        "sku": "SKU-TEST-001",
        "name": "Organic Green Tea 100g",
        "category": "Beverages",
        "cost_price": 75.0,
        "selling_price": 120.0,
        "current_stock": 50,
        "safety_stock": 15,
        "created_at": "2026-09-22 10:00:00"
    }

    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.lastrowid = 21
    mock_db.cursor.return_value.__enter__.return_value = mock_cursor

    def side_effect_query(sql, params=None, one=False):
        if "FROM stores" in sql:
            return mock_store
        if "FROM products WHERE sku" in sql:
            return None  # No duplicate
        if "WHERE p.product_id = %s" in sql:
            return mock_created
        return None

    with patch("app.routes.products.get_db", return_value=mock_db), \
         patch("app.routes.products.query_db", side_effect=side_effect_query):
        res = client.post("/api/products", json=payload)
        assert res.status_code == 201
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["data"]["sku"] == "SKU-TEST-001"

def test_create_product_duplicate_sku(client):
    """Verifies POST /api/products rejects duplicate SKU with 409 Conflict."""
    payload = {
        "sku": "SKU-BEV-001",
        "name": "Another Chai",
        "category": "Beverages",
        "cost_price": 50.0,
        "selling_price": 80.0
    }
    
    def side_effect_query(sql, params=None, one=False):
        if "FROM stores" in sql:
            return {"store_id": 1}
        if "FROM products WHERE sku" in sql:
            return {"product_id": 1}  # Existing SKU found
        return None

    with patch("app.routes.products.query_db", side_effect=side_effect_query):
        res = client.post("/api/products", json=payload)
        assert res.status_code == 409
        assert "already exists" in res.get_json()["message"]

def test_create_product_negative_price(client):
    """Verifies POST /api/products rejects negative price inputs with 400 Bad Request."""
    payload = {
        "sku": "SKU-ERR-001",
        "name": "Invalid Price Item",
        "category": "Beverages",
        "cost_price": -10.0,
        "selling_price": 50.0
    }
    res = client.post("/api/products", json=payload)
    assert res.status_code == 400
    assert "cannot be negative" in res.get_json()["message"]

def test_delete_product_blocked_by_sales_history(client):
    """Verifies DELETE /api/products/<id> blocks deletion if product has sales transactions."""
    mock_existing = {"product_id": 1, "name": "Masala Chai", "sku": "SKU-BEV-001"}
    mock_sales_cnt = {"cnt": 15}

    def side_effect_query(sql, params=None, one=False):
        if "FROM products WHERE product_id" in sql:
            return mock_existing
        if "FROM sale_items WHERE product_id" in sql:
            return mock_sales_cnt
        return None

    with patch("app.routes.products.query_db", side_effect=side_effect_query):
        res = client.delete("/api/products/1")
        assert res.status_code == 409
        assert "Cannot delete" in res.get_json()["message"]
        assert "sales transaction records" in res.get_json()["message"]

def test_delete_product_safe_success(client):
    """Verifies DELETE /api/products/<id> deletes successfully when no sales history exists."""
    mock_existing = {"product_id": 99, "name": "Unsold Item", "sku": "SKU-NEW-099"}
    mock_sales_cnt = {"cnt": 0}

    def side_effect_query(sql, params=None, one=False):
        if "FROM products WHERE product_id" in sql:
            return mock_existing
        if "FROM sale_items WHERE product_id" in sql:
            return mock_sales_cnt
        return None

    with patch("app.routes.products.query_db", side_effect=side_effect_query), \
         patch("app.routes.products.execute_db", return_value={"rowcount": 1}):
        res = client.delete("/api/products/99")
        assert res.status_code == 200
        assert "successfully deleted" in res.get_json()["message"]
