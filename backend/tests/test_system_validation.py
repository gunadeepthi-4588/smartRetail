"""
SmartRetail Phase 15 System Validation & Quality Assurance Test Suite
Thoroughly verifies end-to-end business workflows, database transaction integrity,
mathematical formulas, security sanitization, and API edge cases.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from app import create_app
from app.services.inventory_intelligence_service import calculate_product_inventory_intelligence
from app.services.monitoring_service import calculate_metrics_from_arrays

@pytest.fixture
def client():
    app = create_app("testing")
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

# ------------------------------------------------------------------------------
# 1. Complete End-to-End Business Workflow Simulation
# ------------------------------------------------------------------------------

def test_full_business_workflow_simulation(client):
    """
    Simulates the full vertical slice:
    1. Product exists with inventory
    2. Sale transaction records and deducts inventory atomically
    3. Analytics reflect revenue and gross profit
    4. ML forecast is generated and stored
    5. Inventory intelligence detects stockout/reorder needs
    6. Recommendation explanation generates mathematical breakdown
    7. Forecast monitoring evaluates predicted vs actual sales
    """
    # Step 1 & 2: Sale Transaction & Atomic Inventory Deduction
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.lastrowid = 1001

    def cursor_execute(sql, params=None):
        if "SELECT store_id" in sql:
            mock_cursor.fetchone.return_value = {"store_id": 1}
        elif "SELECT p.product_id" in sql:
            mock_cursor.fetchone.return_value = {
                "product_id": 1,
                "name": "Masala Chai Tea Bags 250g",
                "sku": "SKU-BEV-001",
                "cost_price": 90.0,
                "selling_price": 135.0,
                "current_stock": 25
            }
        elif "SELECT sale_id FROM sales WHERE receipt_number" in sql:
            mock_cursor.fetchone.return_value = None

    mock_cursor.execute.side_effect = cursor_execute
    mock_db.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("app.routes.sales.get_db", return_value=mock_db):
        sale_res = client.post("/api/sales", json={
            "store_id": 1,
            "payment_method": "UPI",
            "items": [{"product_id": 1, "quantity": 5, "unit_price": 135.0}]
        })
        assert sale_res.status_code == 201
        sale_data = sale_res.get_json()
        assert sale_data["status"] == "success"
        assert sale_data["data"]["total_amount"] == 675.0
        mock_db.commit.assert_called_once()

    # Step 3: Analytics Verification
    mock_today = {"today_revenue": 675.0, "today_transactions": 1}
    mock_30d = {
        "revenue_30d": 675.0,
        "gross_profit_30d": 225.0,
        "units_sold_30d": 5,
        "transactions_30d": 1
    }
    mock_inventory = [
        {"product_id": 1, "cost_price": 90.0, "selling_price": 135.0, "current_stock": 20, "min_stock_level": 10, "max_stock_level": 100, "safety_stock": 10}
    ]
    mock_slow = {"slow_moving_count": 0}

    def an_side_effect(sql, params=None, one=False):
        if "DATE(sale_date) = CURDATE()" in sql:
            return mock_today if one else [mock_today]
        elif "revenue_30d" in sql:
            return mock_30d if one else [mock_30d]
        elif "slow_moving_count" in sql:
            return mock_slow if one else [mock_slow]
        elif "FROM products p" in sql and "JOIN inventory i" in sql:
            return mock_inventory[0] if one else mock_inventory
        return None

    with patch("app.routes.analytics.query_db", side_effect=an_side_effect):
        analytics_res = client.get("/api/analytics/dashboard")
        assert analytics_res.status_code == 200
        an_data = analytics_res.get_json()["data"]
        assert an_data["financial_kpis"]["today_revenue"] == 675.0
        assert an_data["financial_kpis"]["gross_profit_30d"] == 225.0

    # Step 4: Forecast Generation & Storage
    mock_forecast = {
        "product": {"product_id": 1, "sku": "SKU-BEV-001", "name": "Masala Chai", "category": "Beverages"},
        "forecast_run_date": "2026-09-21",
        "horizon_days": 7,
        "model_name": "Random Forest (trees=50, depth=6)",
        "total_projected_demand": 28.0,
        "avg_daily_projected_demand": 4.0,
        "predictions": [{"target_date": f"2026-09-{22+i}", "predicted_demand": 4.0, "day_of_week": "Tuesday"} for i in range(7)]
    }
    with patch("app.routes.forecast.generate_and_save_forecast", return_value=mock_forecast):
        fc_res = client.post("/api/forecast", json={"product_id": 1, "horizon_days": 7})
        assert fc_res.status_code == 201
        assert fc_res.get_json()["data"]["total_projected_demand"] == 28.0

    # Step 5 & 6: Inventory Intelligence & Explainable Reorder Recommendation
    mock_item = {
        "product_id": 1,
        "sku": "SKU-BEV-001",
        "product_name": "Masala Chai Tea Bags",
        "category": "Beverages",
        "cost_price": 90.0,
        "selling_price": 135.0,
        "current_stock": 20,
        "min_stock_level": 10,
        "max_stock_level": 100,
        "configured_safety_stock": 10,
        "lead_time_days": 2
    }
    mock_forecasts = [{"target_date": f"2026-09-{22+i}", "predicted_demand": 4.0} for i in range(7)]
    mock_sales_30d = {"units_30d": 60}

    def intel_side_effect(sql, params=None, one=False):
        if "FROM products p" in sql:
            return mock_item if one else [mock_item]
        elif "FROM forecasts" in sql:
            return mock_forecasts
        elif "FROM sales s" in sql:
            return mock_sales_30d if one else [mock_sales_30d]
        return None

    with patch("app.services.inventory_intelligence_service.query_db", side_effect=intel_side_effect), \
         patch("app.services.inventory_intelligence_service.get_db"):
        rec = calculate_product_inventory_intelligence(product_id=1, horizon_days=7)
        # Required: 28 + 10 = 38; Current: 20 -> Reorder: 18 units
        assert rec["recommended_quantity"] == 18
        assert rec["recommendation_status"] == "REORDER"
        assert rec["explanation"]["reorder"]["recommended"] is True
        assert rec["explanation"]["reorder"]["recommended_quantity"] == 18
        assert rec["explanation"]["decision_protocol"]["human_in_the_loop"] is True

    # Step 7: Forecast Monitoring
    # Actual sales: 5 units vs predicted 4 units
    eval_metrics = calculate_metrics_from_arrays(y_true=[5.0], y_pred=[4.0])
    assert eval_metrics["mae"] == 1.0
    assert eval_metrics["bias"] == -1.0  # predicted (4) - actual (5) = -1.0 (slight under-prediction)


# ------------------------------------------------------------------------------
# 2. Database Multi-Item Transaction Atomic Rollback Test
# ------------------------------------------------------------------------------

def test_sale_multi_item_atomic_rollback(client):
    """
    Critical Test: A multi-item sale where item 2 has insufficient stock.
    Verifies that NO items are deducted, NO sale record is created, and rollback is triggered.
    """
    mock_db = MagicMock()
    mock_cursor = MagicMock()

    def cursor_execute(sql, params=None):
        if "SELECT store_id" in sql:
            mock_cursor.fetchone.return_value = {"store_id": 1}
        elif "SELECT p.product_id" in sql and params and params[0] == 1:
            # Product 1 has plenty of stock (50 units)
            mock_cursor.fetchone.return_value = {
                "product_id": 1, "name": "Masala Chai", "sku": "SKU-BEV-001",
                "cost_price": 90.0, "selling_price": 135.0, "current_stock": 50
            }
        elif "SELECT p.product_id" in sql and params and params[0] == 2:
            # Product 2 has insufficient stock (only 2 units, but requested 10)
            mock_cursor.fetchone.return_value = {
                "product_id": 2, "name": "Green Tea", "sku": "SKU-BEV-002",
                "cost_price": 110.0, "selling_price": 165.0, "current_stock": 2
            }
        elif "SELECT sale_id FROM sales WHERE receipt_number" in sql:
            mock_cursor.fetchone.return_value = None

    mock_cursor.execute.side_effect = cursor_execute
    mock_db.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("app.routes.sales.get_db", return_value=mock_db):
        res = client.post("/api/sales", json={
            "store_id": 1,
            "payment_method": "Cash",
            "items": [
                {"product_id": 1, "quantity": 5, "unit_price": 135.0},
                {"product_id": 2, "quantity": 10, "unit_price": 165.0}  # Will fail!
            ]
        })
        assert res.status_code == 400
        data = res.get_json()
        assert data["status"] == "error"
        assert "Insufficient stock" in data["message"]
        # Ensure transaction was rolled back and NOT committed
        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()


# ------------------------------------------------------------------------------
# 3. Business Formula Mathematical Verifications
# ------------------------------------------------------------------------------

def test_business_formula_gross_profit_accuracy():
    """Verifies Gross Profit = SUM(quantity * (unit_price - unit_cost))."""
    items = [
        {"qty": 10, "price": 100.0, "cost": 60.0}, # profit: 400
        {"qty": 5, "price": 50.0, "cost": 30.0},   # profit: 100
        {"qty": 2, "price": 200.0, "cost": 150.0}  # profit: 100
    ]
    total_rev = sum(i["qty"] * i["price"] for i in items)
    total_cost = sum(i["qty"] * i["cost"] for i in items)
    gross_profit = sum(i["qty"] * (i["price"] - i["cost"]) for i in items)

    assert total_rev == 1650.0
    assert total_cost == 1050.0
    assert gross_profit == 600.0
    margin_pct = round((gross_profit / total_rev) * 100, 2)
    assert margin_pct == 36.36

def test_business_formula_non_negative_reorder():
    """Verifies recommended reorder quantity is strictly non-negative (max(0, required - current))."""
    mock_item = {
        "product_id": 1,
        "sku": "SKU-1",
        "product_name": "Item",
        "category": "General",
        "cost_price": 10.0,
        "selling_price": 20.0,
        "current_stock": 100,
        "min_stock_level": 5,
        "max_stock_level": 200,
        "configured_safety_stock": 10,
        "lead_time_days": 2
    }
    mock_forecasts = [{"target_date": "2026-09-22", "predicted_demand": 5.0}]
    mock_sales_30d = {"units_30d": 20}

    def intel_side_effect(sql, params=None, one=False):
        if "FROM products p" in sql:
            return mock_item if one else [mock_item]
        elif "FROM forecasts" in sql:
            return mock_forecasts
        elif "FROM sales s" in sql:
            return mock_sales_30d if one else [mock_sales_30d]
        return None

    with patch("app.services.inventory_intelligence_service.query_db", side_effect=intel_side_effect), \
         patch("app.services.inventory_intelligence_service.get_db"):
        rec = calculate_product_inventory_intelligence(product_id=1, horizon_days=7)
        # Required = 5 + 10 = 15; Current = 100 -> Reorder = max(0, 15 - 100) = 0
        assert rec["recommended_quantity"] == 0
        assert rec["recommendation_status"] == "NO_REORDER"
        assert rec["explanation"]["reorder"]["recommended"] is False


# ------------------------------------------------------------------------------
# 4. API Error Handling & Security Sanitization Tests
# ------------------------------------------------------------------------------

def test_error_handling_invalid_endpoints(client):
    """Verifies that non-existent routes return structured 404 JSON with no stack trace."""
    res = client.get("/api/nonexistent_route")
    assert res.status_code == 404
    data = res.get_json()
    assert data["status"] == "error"
    assert data["message"] == "Resource not found"

def test_error_handling_products_invalid_id_format(client):
    """Verifies requesting a non-integer product ID produces a controlled 404 or 400 error."""
    res = client.get("/api/products/invalid_abc")
    assert res.status_code in [400, 404]
    data = res.get_json()
    assert data["status"] == "error"

def test_error_handling_invalid_payloads_create_product(client):
    """Verifies POST /api/products returns 400 for negative prices or empty names."""
    # Negative price
    res_neg = client.post("/api/products", json={
        "sku": "TEST-SKU-999",
        "name": "Test Item",
        "category": "Snacks",
        "cost_price": -10.0,
        "selling_price": 20.0
    })
    assert res_neg.status_code == 400
    assert "Prices cannot be negative" in res_neg.get_json()["message"]

    # Missing SKU
    res_nosku = client.post("/api/products", json={
        "name": "Test Item",
        "category": "Snacks",
        "cost_price": 10.0,
        "selling_price": 20.0
    })
    assert res_nosku.status_code == 400
    assert "sku" in res_nosku.get_json()["message"]

