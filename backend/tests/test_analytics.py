import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from datetime import datetime

@pytest.fixture
def client():
    app = create_app("testing")
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_get_dashboard_kpis(client):
    """Verifies GET /api/analytics/dashboard aggregates revenue, profit, units, and inventory health."""
    mock_today = {"today_revenue": 1620.0, "today_transactions": 2}
    mock_30d = {
        "revenue_30d": 37685.0,
        "gross_profit_30d": 11493.0,
        "units_sold_30d": 247,
        "transactions_30d": 30
    }
    mock_inventory = [
        {"product_id": 1, "cost_price": 90.0, "selling_price": 135.0, "current_stock": 25, "min_stock_level": 10, "max_stock_level": 100, "safety_stock": 20},
        {"product_id": 2, "cost_price": 420.0, "selling_price": 560.0, "current_stock": 8, "min_stock_level": 10, "max_stock_level": 80, "safety_stock": 15}, # Low stock
        {"product_id": 3, "cost_price": 50.0, "selling_price": 75.0, "current_stock": 0, "min_stock_level": 5, "max_stock_level": 50, "safety_stock": 10}, # Out of stock
        {"product_id": 4, "cost_price": 30.0, "selling_price": 50.0, "current_stock": 250, "min_stock_level": 20, "max_stock_level": 200, "safety_stock": 40} # Overstock
    ]
    mock_slow = {"slow_moving_count": 2}

    def side_effect(sql, params=None, one=False):
        if "DATE(sale_date) = CURDATE()" in sql:
            return mock_today if one else [mock_today]
        elif "revenue_30d" in sql:
            return mock_30d if one else [mock_30d]
        elif "slow_moving_count" in sql:
            return mock_slow if one else [mock_slow]
        elif "FROM products p" in sql and "JOIN inventory i" in sql:
            return mock_inventory[0] if one else mock_inventory
        return None

    with patch("app.routes.analytics.query_db", side_effect=side_effect):
        res = client.get("/api/analytics/dashboard")
        assert res.status_code == 200
        data = res.get_json()["data"]

        # Verify Financial KPIs
        assert data["financial_kpis"]["today_revenue"] == 1620.0
        assert data["financial_kpis"]["revenue_30d"] == 37685.0
        assert data["financial_kpis"]["gross_profit_30d"] == 11493.0
        assert data["financial_kpis"]["units_sold_30d"] == 247
        assert data["financial_kpis"]["transactions_30d"] == 30
        assert round(data["financial_kpis"]["gross_margin_pct_30d"], 1) == 30.5

        # Verify Inventory KPIs
        assert data["inventory_kpis"]["total_products"] == 4
        assert data["inventory_kpis"]["out_of_stock_count"] == 1
        assert data["inventory_kpis"]["low_stock_count"] == 1
        assert data["inventory_kpis"]["overstock_count"] == 1
        assert data["inventory_kpis"]["healthy_stock_count"] == 1
        assert data["inventory_kpis"]["slow_moving_count"] == 2

def test_sales_trend_time_range(client):
    """Verifies GET /api/analytics/sales-trend handles 7, 30, and 90 day ranges and fills missing dates."""
    mock_trend_rows = [
        {
            "sale_date_str": "2026-09-20",
            "daily_revenue": 1620.0,
            "daily_profit": 510.0,
            "daily_units": 15,
            "daily_transactions": 2
        },
        {
            "sale_date_str": "2026-09-21",
            "daily_revenue": 2100.0,
            "daily_profit": 700.0,
            "daily_units": 20,
            "daily_transactions": 3
        }
    ]
    with patch("app.routes.analytics.query_db", return_value=mock_trend_rows):
        res = client.get("/api/analytics/sales-trend?days=7")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["time_range_days"] == 7
        assert len(json_data["data"]) == 7  # 7 days filled continuous time series

def test_top_products_distinct_rankings(client):
    """
    Verifies that Best-Sellers (Units), Revenue Leaders, and Profit Leaders
    are computed with separate, distinct rankings and formulas.
    """
    mock_products = [
        {
            "product_id": 1,
            "product_name": "Potato Crisps 100g",
            "sku": "SKU-SNK-001",
            "category": "Snacks",
            "total_units_sold": 100,  # Top units
            "total_revenue": 2000.0,
            "gross_profit": 500.0
        },
        {
            "product_id": 2,
            "product_name": "Basmati Rice 5kg",
            "sku": "SKU-GRN-001",
            "category": "Grains",
            "total_units_sold": 20,
            "total_revenue": 11200.0,  # Top revenue
            "gross_profit": 2800.0     # Top profit
        },
        {
            "product_id": 3,
            "product_name": "Filter Coffee 500g",
            "sku": "SKU-BEV-002",
            "category": "Beverages",
            "total_units_sold": 15,
            "total_revenue": 4500.0,
            "gross_profit": 1500.0
        }
    ]

    with patch("app.routes.analytics.query_db", return_value=mock_products):
        res = client.get("/api/analytics/top-products?days=30&limit=3")
        assert res.status_code == 200
        data = res.get_json()["data"]

        # Best-Seller #1 must be Potato Crisps (100 units)
        assert data["best_sellers"][0]["name"] == "Potato Crisps 100g"
        assert data["best_sellers"][0]["units_sold"] == 100

        # Revenue Leader #1 must be Basmati Rice (₹11,200.00)
        assert data["revenue_leaders"][0]["name"] == "Basmati Rice 5kg"
        assert data["revenue_leaders"][0]["revenue"] == 11200.0

        # Profit Leader #1 must be Basmati Rice (₹2,800.00 profit, 25.0% margin)
        assert data["profit_leaders"][0]["name"] == "Basmati Rice 5kg"
        assert data["profit_leaders"][0]["gross_profit"] == 2800.0
        assert data["profit_leaders"][0]["gross_margin_pct"] == 25.0

def test_slow_movers_calculation(client):
    """Verifies GET /api/analytics/slow-movers flags dormant inventory with holding valuation."""
    mock_slow_rows = [
        {
            "product_id": 15,
            "product_name": "Microfiber Cloth 3-Pack",
            "sku": "SKU-CLN-001",
            "category": "Cleaning",
            "cost_price": 60.0,
            "selling_price": 95.0,
            "current_stock": 165,
            "safety_stock": 20,
            "last_sale_date": datetime(2026, 7, 10, 14, 0, 0),
            "days_since_last_sale": 74,
            "recent_units_sold": 0
        },
        {
            "product_id": 18,
            "product_name": "Herbal Conditioner 200ml",
            "sku": "SKU-PC-003",
            "category": "Personal Care",
            "cost_price": 120.0,
            "selling_price": 180.0,
            "current_stock": 40,
            "safety_stock": 15,
            "last_sale_date": None,
            "days_since_last_sale": None,
            "recent_units_sold": 0
        }
    ]

    with patch("app.routes.analytics.query_db", return_value=mock_slow_rows):
        res = client.get("/api/analytics/slow-movers?days_threshold=30")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["total_slow_movers"] == 2

        # Item 1: 165 units * 60.0 cost = 9900.0 holding value
        assert json_data["data"][0]["name"] == "Microfiber Cloth 3-Pack"
        assert json_data["data"][0]["inventory_holding_value"] == 9900.0
        assert json_data["data"][0]["days_since_last_sale"] == 74
        assert json_data["data"][0]["never_sold"] is False

        # Item 2: Never sold
        assert json_data["data"][1]["name"] == "Herbal Conditioner 200ml"
        assert json_data["data"][1]["never_sold"] is True
        assert json_data["data"][1]["inventory_holding_value"] == 4800.0

def test_category_performance(client):
    """Verifies GET /api/analytics/category-performance aggregates revenue and margin by category."""
    mock_cats = [
        {
            "category": "Grains & Staples",
            "product_count": 4,
            "units_sold": 45,
            "category_revenue": 14500.0,
            "category_profit": 3600.0
        },
        {
            "category": "Beverages",
            "product_count": 3,
            "units_sold": 60,
            "category_revenue": 8100.0,
            "category_profit": 2700.0
        }
    ]

    with patch("app.routes.analytics.query_db", return_value=mock_cats):
        res = client.get("/api/analytics/category-performance?days=30")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 2
        assert json_data["data"][0]["category"] == "Grains & Staples"
        assert json_data["data"][0]["gross_margin_pct"] == round(3600.0 / 14500.0 * 100, 2)
