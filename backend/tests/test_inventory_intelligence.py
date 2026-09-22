import pytest
import math
from unittest.mock import patch, MagicMock
from app import create_app
from app.services.inventory_intelligence_service import (
    calculate_volatility_safety_stock,
    calculate_product_inventory_intelligence
)

@pytest.fixture
def client():
    app = create_app("testing")
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

# ------------------------------------------------------------------------------
# 1. Unit Tests for Calculations & Edge Cases
# ------------------------------------------------------------------------------
def test_safety_stock_volatility_calculation():
    """Verifies safety stock fallback formula: ceil(Z * std_dev * sqrt(lead_time))."""
    # Mock daily sales with known standard deviation
    mock_sales = [
        {"sale_date_str": "2026-09-01", "daily_qty": 4},
        {"sale_date_str": "2026-09-02", "daily_qty": 6},
        {"sale_date_str": "2026-09-03", "daily_qty": 5},
        {"sale_date_str": "2026-09-04", "daily_qty": 5}
    ]
    with patch("app.services.inventory_intelligence_service.query_db", return_value=mock_sales):
        ss, std_dev, estimated = calculate_volatility_safety_stock(product_id=1, lead_time_days=4, z_value=1.65)
        # std_dev for [4,6,5,5] is approx 0.816
        # Z * std * sqrt(4) = 1.65 * 0.816 * 2 = 2.69 -> ceil = 3
        assert estimated is True
        assert ss == 3

def test_reorder_when_stock_insufficient(client):
    """
    Verifies Reorder recommendation when stock is lower than required stock:
    Required = Forecast (25) + Safety (10) = 35. Current Stock = 12.
    Recommended = 35 - 12 = 23 (Status: REORDER).
    Stockout risk = True since current stock (12) < lead-time demand (15) + safety (10) = 25.
    """
    mock_item = {
        "product_id": 1,
        "sku": "SKU-BEV-001",
        "product_name": "Masala Chai Tea Bags",
        "category": "Beverages",
        "cost_price": 90.0,
        "selling_price": 135.0,
        "current_stock": 12,
        "min_stock_level": 10,
        "max_stock_level": 100,
        "configured_safety_stock": 10,
        "lead_time_days": 3
    }
    mock_forecasts = [
        {"target_date": "2026-09-21", "predicted_demand": 5.0},
        {"target_date": "2026-09-22", "predicted_demand": 5.0},
        {"target_date": "2026-09-23", "predicted_demand": 5.0},
        {"target_date": "2026-09-24", "predicted_demand": 3.0},
        {"target_date": "2026-09-25", "predicted_demand": 3.0},
        {"target_date": "2026-09-26", "predicted_demand": 2.0},
        {"target_date": "2026-09-27", "predicted_demand": 2.0},
    ] # Total 7-day forecast = 25.0. Lead-time demand (first 3 days) = 15.0

    mock_sales_30d = {"units_30d": 60}

    def side_effect(sql, params=None, one=False):
        if "FROM products p\n        JOIN inventory i" in sql or "FROM products p JOIN inventory i" in sql:
            return mock_item if one else [mock_item]
        elif "FROM forecasts" in sql:
            return mock_forecasts
        elif "FROM sales s\n        JOIN sale_items si" in sql or "FROM sales s JOIN sale_items si" in sql:
            return mock_sales_30d if one else [mock_sales_30d]
        return None

    with patch("app.services.inventory_intelligence_service.query_db", side_effect=side_effect):
        with patch("app.services.inventory_intelligence_service.get_db"):
            intel = calculate_product_inventory_intelligence(product_id=1, horizon_days=7)

            assert intel["current_stock"] == 12
            assert intel["safety_stock"] == 10
            assert intel["forecasted_demand"] == 25.0
            assert intel["lead_time_demand"] == 15.0
            assert intel["required_stock"] == 35.0
            assert intel["stockout_risk"] is True
            assert intel["stockout_gap"] == 13.0 # (15 + 10) - 12 = 13.0
            assert intel["recommended_quantity"] == 23 # 35 - 12 = 23
            assert intel["recommendation_status"] == "REORDER"

def test_reorder_when_stock_sufficient(client):
    """
    Verifies Reorder recommendation when current stock is ample:
    Required = Forecast (14) + Safety (10) = 24. Current Stock = 50.
    Recommended = max(0, 24 - 50) = 0 (Status: NO_REORDER).
    Stockout risk = False.
    """
    mock_item = {
        "product_id": 2,
        "sku": "SKU-BEV-002",
        "product_name": "Arabica Coffee 500g",
        "category": "Beverages",
        "cost_price": 220.0,
        "selling_price": 330.0,
        "current_stock": 50,
        "min_stock_level": 15,
        "max_stock_level": 80,
        "configured_safety_stock": 10,
        "lead_time_days": 2
    }
    mock_forecasts = [
        {"target_date": f"2026-09-{21+i}", "predicted_demand": 2.0}
        for i in range(7)
    ] # Total 7-day forecast = 14.0. Lead-time demand = 4.0
    mock_sales_30d = {"units_30d": 40}

    def side_effect(sql, params=None, one=False):
        if "FROM products p" in sql and "inventory i" in sql:
            return mock_item if one else [mock_item]
        elif "FROM forecasts" in sql:
            return mock_forecasts
        elif "FROM sales s" in sql:
            return mock_sales_30d if one else [mock_sales_30d]
        return None

    with patch("app.services.inventory_intelligence_service.query_db", side_effect=side_effect):
        with patch("app.services.inventory_intelligence_service.get_db"):
            intel = calculate_product_inventory_intelligence(product_id=2, horizon_days=7)

            assert intel["current_stock"] == 50
            assert intel["forecasted_demand"] == 14.0
            assert intel["required_stock"] == 24.0
            assert intel["stockout_risk"] is False
            assert intel["stockout_gap"] == 0.0
            assert intel["recommended_quantity"] == 0
            assert intel["recommendation_status"] == "NO_REORDER"

def test_overstock_detection(client):
    """
    Verifies Overstock detection when current stock exceeds 1.5x of 30-day demand:
    30-day demand = 10 units -> Overstock Threshold = 10 * 1.5 = 15 units.
    Current Stock = 80 units -> overstock_risk = True.
    """
    mock_item = {
        "product_id": 20,
        "sku": "SKU-CLN-001",
        "product_name": "Microfiber Cloth 3-Pack",
        "category": "Cleaning",
        "cost_price": 60.0,
        "selling_price": 95.0,
        "current_stock": 80,
        "min_stock_level": 10,
        "max_stock_level": 50,
        "configured_safety_stock": 5,
        "lead_time_days": 3
    }
    mock_forecasts = [{"target_date": f"2026-09-{21+i}", "predicted_demand": 0.5} for i in range(7)]
    mock_sales_30d = {"units_30d": 10} # Overstock threshold = 15

    def side_effect(sql, params=None, one=False):
        if "FROM products p" in sql and "inventory i" in sql:
            return mock_item if one else [mock_item]
        elif "FROM forecasts" in sql:
            return mock_forecasts
        elif "FROM sales s" in sql:
            return mock_sales_30d if one else [mock_sales_30d]
        return None

    with patch("app.services.inventory_intelligence_service.query_db", side_effect=side_effect):
        with patch("app.services.inventory_intelligence_service.get_db"):
            intel = calculate_product_inventory_intelligence(product_id=20, horizon_days=7)

            assert intel["overstock_risk"] is True
            assert intel["overstock_threshold"] == 15.0
            assert intel["current_stock"] == 80

# ------------------------------------------------------------------------------
# 2. HTTP Endpoint Tests
# ------------------------------------------------------------------------------
def test_api_inventory_intelligence_endpoint(client):
    """Verifies GET /api/inventory/intelligence returns list of product intelligence."""
    mock_list = [
        {
            "product_id": 1,
            "sku": "SKU-BEV-001",
            "name": "Masala Chai Tea Bags",
            "current_stock": 12,
            "safety_stock": 10,
            "lead_time_demand": 15.0,
            "forecasted_demand": 25.0,
            "required_stock": 35.0,
            "stockout_risk": True,
            "recommended_quantity": 23,
            "recommendation_status": "REORDER"
        }
    ]
    with patch("app.routes.recommendations.get_all_inventory_intelligence", return_value=mock_list):
        res = client.get("/api/inventory/intelligence?days=7")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["count"] == 1
        assert json_data["data"][0]["recommendation_status"] == "REORDER"

def test_api_inventory_intelligence_invalid_days(client):
    """Verifies GET /api/inventory/intelligence rejects invalid horizon parameter (e.g. days=15)."""
    res = client.get("/api/inventory/intelligence?days=15")
    assert res.status_code == 400
    assert "days must be either 7 or 30" in res.get_json()["message"]

def test_api_recommendations_filter(client):
    """Verifies GET /api/recommendations?status=REORDER filters products correctly."""
    mock_all = [
        {"product_id": 1, "name": "P1", "recommendation_status": "REORDER", "recommended_quantity": 15},
        {"product_id": 2, "name": "P2", "recommendation_status": "NO_REORDER", "recommended_quantity": 0}
    ]
    with patch("app.routes.recommendations.get_all_inventory_intelligence", return_value=mock_all):
        res = client.get("/api/recommendations?status=REORDER")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["count"] == 1
        assert json_data["data"][0]["name"] == "P1"
