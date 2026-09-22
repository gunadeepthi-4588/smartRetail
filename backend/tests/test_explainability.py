import pytest
from unittest.mock import patch
from app import create_app
from app.services.inventory_intelligence_service import calculate_product_inventory_intelligence

@pytest.fixture
def client():
    app = create_app("testing")
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_explainable_positive_reorder_and_stockout():
    """
    Verifies that a product with low stock generates transparent explainability
    for both Reorder recommendation and Stockout risk.
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
        "configured_safety_stock": 8,
        "lead_time_days": 5
    }
    mock_forecasts = [
        {"target_date": f"2026-09-{21+i}", "predicted_demand": 4.0}
        for i in range(7)
    ] # 7D Forecast = 28.0. Lead-time demand (5 days) = 20.0
    mock_sales_30d = {"units_30d": 60}

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
            intel = calculate_product_inventory_intelligence(product_id=1, horizon_days=7)
            exp = intel["explanation"]

            # 1. Reorder Explanation Checks
            assert exp["reorder"]["recommended"] is True
            assert exp["reorder"]["recommended_quantity"] == 24 # Required (28+8=36) - 12 = 24
            assert exp["reorder"]["required_stock"] == 36.0
            assert exp["reorder"]["stock_on_order"] == 0
            assert "Expected demand" in exp["reorder"]["reason"]
            assert "higher than current available stock" in exp["reorder"]["reason"]
            assert "Purchase order tracking is not implemented" in exp["reorder"]["mvp_assumption"]

            # 2. Stockout Risk Explanation Checks
            assert exp["stockout_risk"]["risk_detected"] is True
            assert exp["stockout_risk"]["lead_time_demand"] == 20.0
            assert exp["stockout_risk"]["safety_stock"] == 8
            assert exp["stockout_risk"]["lead_time_required_stock"] == 28.0 # 20 + 8
            assert exp["stockout_risk"]["stockout_gap"] == 16.0 # 28 - 12
            assert "Stockout risk is detected" in exp["stockout_risk"]["reason"]

            # 3. Configured Safety Stock Explanation Checks
            assert exp["safety_stock"]["source"] == "configured_inventory_safety_stock"
            assert "configured for this product" in exp["safety_stock"]["reason"]

            # 4. Consistency: Explanation values strictly match root values
            assert exp["reorder"]["recommended_quantity"] == intel["recommended_quantity"]
            assert exp["reorder"]["required_stock"] == intel["required_stock"]
            assert exp["stockout_risk"]["stockout_gap"] == intel["stockout_gap"]

def test_explainable_no_reorder_and_overstock():
    """
    Verifies that an overstocked item with high stock generates transparent explainability
    for NO_REORDER and Overstock risk warning.
    """
    mock_item = {
        "product_id": 20,
        "sku": "SKU-CLN-001",
        "product_name": "Microfiber Cloth 3-Pack",
        "category": "Cleaning",
        "cost_price": 60.0,
        "selling_price": 95.0,
        "current_stock": 165,
        "min_stock_level": 10,
        "max_stock_level": 50,
        "configured_safety_stock": 10,
        "lead_time_days": 3
    }
    mock_forecasts = [
        {"target_date": f"2026-09-{21+i}", "predicted_demand": 0.5}
        for i in range(7)
    ] # 7D Forecast = 3.5. Required = 13.5
    mock_sales_30d = {"units_30d": 15} # Overstock threshold = 15 * 1.5 = 22.5

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
            exp = intel["explanation"]

            # 1. No-Reorder Checks
            assert exp["reorder"]["recommended"] is False
            assert exp["reorder"]["recommended_quantity"] == 0
            assert "sufficient to cover expected" in exp["reorder"]["reason"]

            # 2. No-Stockout Checks
            assert exp["stockout_risk"]["risk_detected"] is False
            assert "covers expected lead-time demand" in exp["stockout_risk"]["reason"]

            # 3. Overstock Checks
            assert exp["overstock_risk"]["risk_detected"] is True
            assert exp["overstock_risk"]["overstock_threshold"] == 22.5
            assert exp["overstock_risk"]["current_stock"] == 165
            assert "above the configured overstock threshold" in exp["overstock_risk"]["reason"]

def test_explainable_safety_stock_fallbacks():
    """Verifies explanation text when safety stock is dynamically computed or falls back due to insufficient data."""
    mock_item = {
        "product_id": 5,
        "sku": "SKU-SNK-005",
        "product_name": "Cashews 200g",
        "category": "Snacks",
        "cost_price": 180.0,
        "selling_price": 260.0,
        "current_stock": 25,
        "min_stock_level": 10,
        "max_stock_level": 70,
        "configured_safety_stock": 0, # Unconfigured -> triggers fallback
        "lead_time_days": 4
    }
    mock_forecasts = [{"target_date": f"2026-09-{21+i}", "predicted_demand": 2.0} for i in range(7)]
    mock_sales_volatility = [
        {"sale_date_str": "2026-09-01", "daily_qty": 2},
        {"sale_date_str": "2026-09-02", "daily_qty": 4},
        {"sale_date_str": "2026-09-03", "daily_qty": 3}
    ]
    mock_sales_30d = {"units_30d": 20}

    def side_effect(sql, params=None, one=False):
        if "FROM products p" in sql and "inventory i" in sql:
            return mock_item if one else [mock_item]
        elif "FROM forecasts" in sql:
            return mock_forecasts
        elif "WHERE si.product_id = %s\n        GROUP BY DATE(s.sale_date)" in sql or "WHERE si.product_id = %s GROUP BY DATE(s.sale_date)" in sql:
            return mock_sales_volatility
        elif "FROM sales s" in sql:
            return mock_sales_30d if one else [mock_sales_30d]
        return None

    with patch("app.services.inventory_intelligence_service.query_db", side_effect=side_effect):
        with patch("app.services.inventory_intelligence_service.get_db"):
            intel = calculate_product_inventory_intelligence(product_id=5, horizon_days=7)
            exp = intel["explanation"]

            assert exp["safety_stock"]["source"] == "dynamic_volatility_fallback"
            assert "Safety stock provides an additional buffer" in exp["safety_stock"]["reason"]
            assert exp["safety_stock"]["lead_time_days"] == 4
            assert exp["safety_stock"]["z_value"] == 1.65
