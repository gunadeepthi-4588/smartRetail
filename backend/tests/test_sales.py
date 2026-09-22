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

def test_get_sales_history(client):
    """Verifies GET /api/sales returns transaction list with line item counts."""
    mock_sales = [
        {
            "sale_id": 30,
            "store_id": 1,
            "receipt_number": "REC-20260920-030",
            "total_amount": 1620.0,
            "payment_method": "Cash",
            "sale_date": "2026-09-20 19:00:00",
            "items_count": 5,
            "total_units_sold": 5
        }
    ]
    with patch("app.routes.sales.query_db", return_value=mock_sales):
        res = client.get("/api/sales")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["count"] == 1
        assert json_data["data"][0]["receipt_number"] == "REC-20260920-030"

def test_get_sale_detail_by_id(client):
    """Verifies GET /api/sales/<id> returns header and line items."""
    mock_header = {
        "sale_id": 1,
        "store_id": 1,
        "receipt_number": "REC-20260822-001",
        "total_amount": 1345.0,
        "payment_method": "UPI",
        "sale_date": "2026-08-22 10:15:00"
    }
    mock_items = [
        {
            "sale_item_id": 1,
            "product_id": 1,
            "sku": "SKU-BEV-001",
            "product_name": "Masala Chai Tea Bags 250g",
            "category": "Beverages",
            "quantity": 3,
            "unit_price": 135.0,
            "unit_cost": 90.0,
            "line_total": 405.0,
            "line_profit": 135.0
        }
    ]

    def side_effect_query(sql, params=None, one=False):
        if "FROM sales" in sql:
            return mock_header
        if "FROM sale_items" in sql:
            return mock_items
        return None

    with patch("app.routes.sales.query_db", side_effect=side_effect_query):
        res = client.get("/api/sales/1")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["data"]["receipt_number"] == "REC-20260822-001"
        assert len(json_data["data"]["items"]) == 1
        assert json_data["data"]["items"][0]["line_total"] == 405.0

def test_create_sale_successful_atomic_transaction(client):
    """Verifies POST /api/sales executes atomic sale creation and inventory deduction."""
    payload = {
        "store_id": 1,
        "payment_method": "UPI",
        "items": [
            {"product_id": 1, "quantity": 2, "unit_price": 135.0},
            {"product_id": 6, "quantity": 3, "unit_price": 35.0}
        ]
    }

    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.lastrowid = 101

    # Product queries return available stock
    def cursor_execute_side_effect(sql, params=None):
        if "SELECT store_id" in sql:
            mock_cursor.fetchone.return_value = {"store_id": 1}
        elif "SELECT p.product_id" in sql and params and params[0] == 1:
            mock_cursor.fetchone.return_value = {
                "product_id": 1, "name": "Masala Chai", "sku": "SKU-BEV-001",
                "cost_price": 90.0, "selling_price": 135.0, "current_stock": 12
            }
        elif "SELECT p.product_id" in sql and params and params[0] == 6:
            mock_cursor.fetchone.return_value = {
                "product_id": 6, "name": "Potato Crisps", "sku": "SKU-SNK-002",
                "cost_price": 20.0, "selling_price": 35.0, "current_stock": 25
            }
        elif "SELECT sale_id FROM sales WHERE receipt_number" in sql:
            mock_cursor.fetchone.return_value = None  # No duplicate receipt

    mock_cursor.execute.side_effect = cursor_execute_side_effect
    mock_db.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("app.routes.sales.get_db", return_value=mock_db):
        res = client.post("/api/sales", json=payload)
        assert res.status_code == 201
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["data"]["total_amount"] == 375.0  # (2 * 135) + (3 * 35) = 270 + 105 = 375
        assert json_data["data"]["items_count"] == 2
        mock_db.commit.assert_called_once()

def test_create_sale_insufficient_inventory(client):
    """Verifies POST /api/sales rejects request when requested quantity exceeds available stock."""
    payload = {
        "store_id": 1,
        "payment_method": "Cash",
        "items": [
            {"product_id": 1, "quantity": 50, "unit_price": 135.0}  # Available is only 12
        ]
    }

    mock_db = MagicMock()
    mock_cursor = MagicMock()

    def cursor_execute_side_effect(sql, params=None):
        if "SELECT store_id" in sql:
            mock_cursor.fetchone.return_value = {"store_id": 1}
        elif "SELECT p.product_id" in sql:
            mock_cursor.fetchone.return_value = {
                "product_id": 1, "name": "Masala Chai", "sku": "SKU-BEV-001",
                "cost_price": 90.0, "selling_price": 135.0, "current_stock": 12
            }

    mock_cursor.execute.side_effect = cursor_execute_side_effect
    mock_db.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("app.routes.sales.get_db", return_value=mock_db):
        res = client.post("/api/sales", json=payload)
        assert res.status_code == 400
        json_data = res.get_json()
        assert "Insufficient stock" in json_data["message"]
        assert "Requested: 50, Available: 12" in json_data["message"]
        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

def test_critical_transaction_rollback_multi_item(client):
    """
    CRITICAL TEST:
    Sale with Product A (sufficient stock) and Product B (insufficient stock).
    Entire transaction must abort and roll back.
    Zero sales, zero sale items, zero inventory deductions.
    """
    payload = {
        "store_id": 1,
        "payment_method": "Card",
        "items": [
            {"product_id": 1, "quantity": 2},   # Product A: Stock is 12 (Sufficient)
            {"product_id": 6, "quantity": 100}  # Product B: Stock is 8 (Insufficient!)
        ]
    }

    mock_db = MagicMock()
    mock_cursor = MagicMock()

    def cursor_execute_side_effect(sql, params=None):
        if "SELECT store_id" in sql:
            mock_cursor.fetchone.return_value = {"store_id": 1}
        elif "SELECT p.product_id" in sql and params and params[0] == 1:
            mock_cursor.fetchone.return_value = {
                "product_id": 1, "name": "Masala Chai", "sku": "SKU-BEV-001",
                "cost_price": 90.0, "selling_price": 135.0, "current_stock": 12
            }
        elif "SELECT p.product_id" in sql and params and params[0] == 6:
            mock_cursor.fetchone.return_value = {
                "product_id": 6, "name": "Potato Crisps", "sku": "SKU-SNK-002",
                "cost_price": 20.0, "selling_price": 35.0, "current_stock": 8
            }

    mock_cursor.execute.side_effect = cursor_execute_side_effect
    mock_db.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("app.routes.sales.get_db", return_value=mock_db):
        res = client.post("/api/sales", json=payload)
        assert res.status_code == 400
        json_data = res.get_json()
        assert "Insufficient stock for 'Potato Crisps'" in json_data["message"]
        # Verify rollback was called and commit was NOT called
        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

def test_create_sale_invalid_payment_method(client):
    """Verifies POST /api/sales rejects invalid payment methods."""
    payload = {
        "store_id": 1,
        "payment_method": "Bitcoin",  # Invalid
        "items": [{"product_id": 1, "quantity": 1}]
    }
    res = client.post("/api/sales", json=payload)
    assert res.status_code == 400
    assert "Invalid payment_method" in res.get_json()["message"]

def test_create_sale_invalid_zero_quantity(client):
    """Verifies POST /api/sales rejects zero or negative quantity."""
    payload = {
        "store_id": 1,
        "payment_method": "Cash",
        "items": [{"product_id": 1, "quantity": 0}]
    }
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {"store_id": 1}
    mock_db.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("app.routes.sales.get_db", return_value=mock_db):
        res = client.post("/api/sales", json=payload)
        assert res.status_code == 400
        assert "greater than zero" in res.get_json()["message"]
