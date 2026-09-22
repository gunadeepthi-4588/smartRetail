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

# ------------------------------------------------------------------------------
# 1. Validation Tests for POST /api/forecast
# ------------------------------------------------------------------------------
def test_create_forecast_missing_product(client):
    """Verifies POST /api/forecast returns 400 when product_id is missing."""
    res = client.post("/api/forecast", json={"horizon_days": 7})
    assert res.status_code == 400
    assert "product_id is required" in res.get_json()["message"]

def test_create_forecast_invalid_horizon(client):
    """Verifies POST /api/forecast returns 400 when horizon_days is not 7 or 30."""
    res = client.post("/api/forecast", json={"product_id": 1, "horizon_days": 15})
    assert res.status_code == 400
    assert "horizon_days must be either 7 or 30" in res.get_json()["message"]

def test_create_forecast_nonexistent_product(client):
    """Verifies POST /api/forecast returns 400 when product does not exist."""
    with patch("app.services.forecast_service.query_db", return_value=None):
        res = client.post("/api/forecast", json={"product_id": 9999, "horizon_days": 7})
        assert res.status_code == 400
        assert "does not exist" in res.get_json()["message"]

def test_create_forecast_valid_7_day(client):
    """Verifies POST /api/forecast succeeds for a valid 7-day request."""
    mock_result = {
        "product": {"product_id": 1, "sku": "SKU-BEV-001", "name": "Masala Chai Tea Bags 250g", "category": "Beverages"},
        "forecast_run_date": "2026-09-20",
        "horizon_days": 7,
        "model_name": "Random Forest (trees=50, depth=6)",
        "total_projected_demand": 21.5,
        "avg_daily_projected_demand": 3.07,
        "predictions": [
            {"target_date": f"2026-09-{21+i}", "predicted_demand": 3.0, "day_of_week": "Monday"}
            for i in range(7)
        ]
    }
    with patch("app.routes.forecast.generate_and_save_forecast", return_value=mock_result):
        res = client.post("/api/forecast", json={"product_id": 1, "horizon_days": 7})
        assert res.status_code == 201
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["data"]["horizon_days"] == 7
        assert len(json_data["data"]["predictions"]) == 7
        assert json_data["data"]["total_projected_demand"] == 21.5

def test_create_forecast_valid_30_day(client):
    """Verifies POST /api/forecast succeeds for a valid 30-day request."""
    mock_result = {
        "product": {"product_id": 6, "sku": "SKU-SNK-001", "name": "Classic Potato Crisps", "category": "Snacks"},
        "forecast_run_date": "2026-09-20",
        "horizon_days": 30,
        "model_name": "Random Forest (trees=50, depth=6)",
        "total_projected_demand": 95.0,
        "avg_daily_projected_demand": 3.17,
        "predictions": [
            {"target_date": f"2026-10-{i:02d}", "predicted_demand": 3.1, "day_of_week": "Friday"}
            for i in range(1, 31)
        ]
    }
    with patch("app.routes.forecast.generate_and_save_forecast", return_value=mock_result):
        res = client.post("/api/forecast", json={"product_id": 6, "horizon_days": 30})
        assert res.status_code == 201
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["data"]["horizon_days"] == 30
        assert len(json_data["data"]["predictions"]) == 30

# ------------------------------------------------------------------------------
# 2. Retrieval Tests for GET /api/forecast
# ------------------------------------------------------------------------------
def test_get_stored_forecasts(client):
    """Verifies GET /api/forecast returns stored forecast records with nullable actual_demand."""
    mock_rows = [
        {
            "forecast_id": 1,
            "product_id": 1,
            "product_name": "Masala Chai Tea Bags 250g",
            "sku": "SKU-BEV-001",
            "category": "Beverages",
            "forecast_date": "2026-09-20",
            "target_date": "2026-09-21",
            "predicted_demand": 3.5,
            "actual_demand": None, # Nullable actual demand
            "model_name": "Random Forest (trees=50, depth=6)",
            "horizon_days": 7,
            "created_at": "2026-09-20 18:00:00"
        }
    ]
    with patch("app.services.forecast_service.query_db", return_value=mock_rows):
        res = client.get("/api/forecast?product_id=1")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["count"] == 1
        assert json_data["data"][0]["actual_demand"] is None
        assert json_data["data"][0]["predicted_demand"] == 3.5

def test_get_product_forecast_and_history(client):
    """Verifies GET /api/forecast/<product_id> returns product metadata, history, and predictions."""
    mock_history_result = {
        "product": {"product_id": 1, "sku": "SKU-BEV-001", "name": "Masala Chai Tea Bags 250g", "category": "Beverages"},
        "has_forecast": True,
        "forecast_run_date": "2026-09-20",
        "model_name": "Random Forest (trees=50, depth=6)",
        "horizon_days": 7,
        "history": [
            {"date": "2026-09-19", "actual_demand": 4},
            {"date": "2026-09-20", "actual_demand": 5}
        ],
        "predictions": [
            {"target_date": "2026-09-21", "predicted_demand": 4.2, "actual_demand": None},
            {"target_date": "2026-09-22", "predicted_demand": 4.0, "actual_demand": None}
        ]
    }
    with patch("app.routes.forecast.get_product_forecast_and_history", return_value=mock_history_result):
        res = client.get("/api/forecast/1?horizon_days=7")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["data"]["has_forecast"] is True
        assert len(json_data["data"]["history"]) == 2
        assert len(json_data["data"]["predictions"]) == 2

def test_update_actual_demands(client):
    """Verifies POST /api/forecast/update-actuals reconciles past forecasts."""
    with patch("app.routes.forecast.update_actual_demand_if_available", return_value=5):
        res = client.post("/api/forecast/update-actuals")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["updated_count"] == 5
