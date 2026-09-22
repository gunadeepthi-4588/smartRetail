import pytest
from unittest.mock import patch
from app import create_app
from app.routes.inventory import calculate_inventory_status

@pytest.fixture
def client():
    app = create_app("testing")
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_inventory_status_calculation():
    """Verifies the core mathematical status logic for inventory items."""
    # 1. Out of Stock
    assert calculate_inventory_status(current_stock=0, min_stock=10, max_stock=100, safety_stock=20) == "Out of Stock"
    assert calculate_inventory_status(current_stock=-5, min_stock=10, max_stock=100, safety_stock=20) == "Out of Stock"

    # 2. Low Stock (Stock < Safety Stock)
    assert calculate_inventory_status(current_stock=12, min_stock=15, max_stock=100, safety_stock=25) == "Low Stock"
    assert calculate_inventory_status(current_stock=8, min_stock=10, max_stock=100, safety_stock=15) == "Low Stock"

    # 3. Overstocked (Stock >= Max Stock)
    assert calculate_inventory_status(current_stock=150, min_stock=10, max_stock=100, safety_stock=20) == "Overstocked"

    # 4. Healthy (Between Safety Stock and Max Stock)
    assert calculate_inventory_status(current_stock=45, min_stock=15, max_stock=100, safety_stock=20) == "Healthy"

def test_get_inventory_all(client):
    """Verifies GET /api/inventory returns full list with computed status and summary metrics."""
    mock_rows = [
        {
            "inventory_id": 1,
            "product_id": 1,
            "sku": "SKU-BEV-001",
            "product_name": "Masala Chai Tea Bags 250g",
            "category": "Beverages",
            "cost_price": 90.0,
            "selling_price": 135.0,
            "current_stock": 12,
            "min_stock_level": 30,
            "max_stock_level": 150,
            "safety_stock": 25,
            "lead_time_days": 2,
            "last_updated": "2026-09-20 18:00:00"
        },
        {
            "inventory_id": 2,
            "product_id": 2,
            "sku": "SKU-BEV-002",
            "product_name": "Arabica Coffee 500g",
            "category": "Beverages",
            "cost_price": 220.0,
            "selling_price": 330.0,
            "current_stock": 45,
            "min_stock_level": 15,
            "max_stock_level": 80,
            "safety_stock": 15,
            "lead_time_days": 2,
            "last_updated": "2026-09-20 18:00:00"
        }
    ]

    with patch("app.routes.inventory.query_db", return_value=mock_rows):
        res = client.get("/api/inventory")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["count"] == 2
        assert "summary" in json_data
        assert json_data["summary"]["low_stock_count"] == 1
        assert json_data["data"][0]["status"] == "Low Stock"
        assert json_data["data"][1]["status"] == "Healthy"

def test_get_inventory_filtered_by_status(client):
    """Verifies GET /api/inventory?status=low returns only low stock items."""
    mock_rows = [
        {
            "inventory_id": 1,
            "product_id": 1,
            "sku": "SKU-BEV-001",
            "product_name": "Masala Chai",
            "category": "Beverages",
            "cost_price": 90.0,
            "selling_price": 135.0,
            "current_stock": 12,
            "min_stock_level": 30,
            "max_stock_level": 150,
            "safety_stock": 25,
            "lead_time_days": 2,
            "last_updated": "2026-09-20 18:00:00"
        },
        {
            "inventory_id": 2,
            "product_id": 2,
            "sku": "SKU-BEV-002",
            "product_name": "Arabica Coffee",
            "category": "Beverages",
            "cost_price": 220.0,
            "selling_price": 330.0,
            "current_stock": 45,
            "min_stock_level": 15,
            "max_stock_level": 80,
            "safety_stock": 15,
            "lead_time_days": 2,
            "last_updated": "2026-09-20 18:00:00"
        }
    ]

    with patch("app.routes.inventory.query_db", return_value=mock_rows):
        res = client.get("/api/inventory?status=low")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["count"] == 1
        assert json_data["data"][0]["sku"] == "SKU-BEV-001"

def test_update_inventory_success(client):
    """Verifies PUT /api/inventory/<id> updates stock levels correctly."""
    mock_existing = {
        "inventory_id": 1,
        "product_id": 1,
        "current_stock": 12,
        "min_stock_level": 30,
        "max_stock_level": 150,
        "safety_stock": 25,
        "lead_time_days": 2
    }
    mock_updated = {
        "inventory_id": 1,
        "product_id": 1,
        "sku": "SKU-BEV-001",
        "product_name": "Masala Chai Tea Bags 250g",
        "category": "Beverages",
        "cost_price": 90.0,
        "selling_price": 135.0,
        "current_stock": 60,
        "min_stock_level": 25,
        "max_stock_level": 150,
        "safety_stock": 25,
        "lead_time_days": 2,
        "last_updated": "2026-09-22 11:00:00"
    }

    def side_effect_query(sql, params=None, one=False):
        if "SELECT * FROM inventory" in sql:
            return mock_existing
        return mock_updated

    with patch("app.routes.inventory.query_db", side_effect=side_effect_query), \
         patch("app.routes.inventory.execute_db", return_value={"rowcount": 1}):
        payload = {
            "current_stock": 60,
            "min_stock_level": 25,
            "max_stock_level": 150,
            "safety_stock": 25,
            "lead_time_days": 2
        }
        res = client.put("/api/inventory/1", json=payload)
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["data"]["current_stock"] == 60
        assert json_data["data"]["status"] == "Healthy"

def test_update_inventory_negative_stock(client):
    """Verifies PUT /api/inventory/<id> rejects negative stock values."""
    mock_existing = {
        "inventory_id": 1,
        "product_id": 1,
        "current_stock": 12,
        "min_stock_level": 30,
        "max_stock_level": 150,
        "safety_stock": 25,
        "lead_time_days": 2
    }
    with patch("app.routes.inventory.query_db", return_value=mock_existing):
        res = client.put("/api/inventory/1", json={"current_stock": -10})
        assert res.status_code == 400
        assert "cannot be negative" in res.get_json()["message"]
