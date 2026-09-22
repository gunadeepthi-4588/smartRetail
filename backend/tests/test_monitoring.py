"""
Tests for Phase 14: Forecast Monitoring & Model Performance Tracking
Tests MAE, RMSE, WAPE, Bias metrics, zero-demand safety, filtering, and API endpoints.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from app import create_app
from app.services.monitoring_service import (
    calculate_metrics_from_arrays,
    get_deterministic_interpretation,
    get_forecast_monitoring_data,
    get_monitoring_summary
)

@pytest.fixture
def client():
    app = create_app("testing")
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

# ------------------------------------------------------------------------------
# 1. Calculation Unit Tests: MAE, RMSE, WAPE, Bias
# ------------------------------------------------------------------------------

def test_mae_calculation():
    """Verifies MAE = mean(|actual - predicted|)."""
    y_true = [10.0, 20.0, 30.0]
    y_pred = [12.0, 18.0, 33.0]
    # abs errors: 2, 2, 3 -> mean = 7/3 = 2.3333
    metrics = calculate_metrics_from_arrays(y_true, y_pred)
    assert metrics["mae"] == round(7.0 / 3.0, 4)
    assert metrics["sample_count"] == 3

def test_rmse_calculation():
    """Verifies RMSE = sqrt(mean((actual - predicted)^2))."""
    y_true = [10.0, 20.0, 30.0]
    y_pred = [12.0, 18.0, 33.0]
    # sq errors: 4, 4, 9 = 17 -> mean = 17/3 -> sqrt = 2.38047
    metrics = calculate_metrics_from_arrays(y_true, y_pred)
    expected_rmse = round(float(np.sqrt(17.0 / 3.0)), 4)
    assert metrics["rmse"] == expected_rmse

def test_wape_calculation():
    """Verifies WAPE = sum(|actual - predicted|) / sum(actual)."""
    y_true = [10.0, 20.0, 30.0]
    y_pred = [12.0, 18.0, 33.0]
    # sum(abs) = 7, sum(actual) = 60 -> WAPE = 7/60 = 0.1167 (11.67%)
    metrics = calculate_metrics_from_arrays(y_true, y_pred)
    assert metrics["wape"] == round(7.0 / 60.0, 4)
    assert metrics["wape_pct"] == 11.67

def test_bias_calculation():
    """Verifies Bias = mean(predicted - actual). Positive = over-forecast, Negative = under-forecast."""
    # Predicted is higher on average:
    y_true = [10.0, 20.0, 30.0]
    y_pred = [15.0, 25.0, 35.0]
    # pred - actual = +5, +5, +5 -> mean = +5.0
    metrics = calculate_metrics_from_arrays(y_true, y_pred)
    assert metrics["bias"] == 5.0

    # Predicted is lower on average:
    y_pred_low = [8.0, 17.0, 26.0]
    # pred - actual = -2, -3, -4 -> mean = -3.0
    metrics_low = calculate_metrics_from_arrays(y_true, y_pred_low)
    assert metrics_low["bias"] == -3.0

def test_zero_actual_demand_handling():
    """Verifies safe handling of zero actual demand without DivisionByZero crash."""
    y_true = [0.0, 0.0, 0.0]
    y_pred = [2.0, 3.0, 1.0]
    metrics = calculate_metrics_from_arrays(y_true, y_pred)
    assert metrics["mae"] == 2.0
    assert metrics["wape"] is None or metrics["wape"] == 0.0
    assert metrics["bias"] == 2.0

    # Exact zero matches
    y_true_zero = [0.0, 0.0]
    y_pred_zero = [0.0, 0.0]
    metrics_zero = calculate_metrics_from_arrays(y_true_zero, y_pred_zero)
    assert metrics_zero["mae"] == 0.0
    assert metrics_zero["wape"] == 0.0

def test_empty_dataset_handling():
    """Verifies graceful handling of empty lists."""
    metrics = calculate_metrics_from_arrays([], [])
    assert metrics["sample_count"] == 0
    assert metrics["mae"] is None
    assert metrics["rmse"] is None
    assert metrics["wape"] is None
    assert metrics["bias"] is None

def test_deterministic_interpretations():
    """Verifies non-judgmental, deterministic interpretations."""
    # Positive bias
    msg_pos = get_deterministic_interpretation(1.5, 20)
    assert "higher than actual demand" in msg_pos

    # Negative bias
    msg_neg = get_deterministic_interpretation(-1.5, 20)
    assert "lower than actual demand" in msg_neg

    # Near zero bias
    msg_zero = get_deterministic_interpretation(0.01, 20)
    assert "close to actual demand" in msg_zero

    # Insufficient samples
    msg_empty = get_deterministic_interpretation(None, 0)
    assert "Insufficient" in msg_empty

# ------------------------------------------------------------------------------
# 2. Service & Aggregation Tests
# ------------------------------------------------------------------------------

def test_monitoring_service_product_filtering():
    """Verifies product_id filtering returns correct records."""
    mock_db_rows = [
        {
            "forecast_id": 1,
            "product_id": 1,
            "product_name": "Masala Chai",
            "sku": "SKU-BEV-001",
            "category": "Beverages",
            "forecast_date": "2026-09-01",
            "target_date": "2026-09-02",
            "predicted_demand": 10.0,
            "actual_demand": 12.0,
            "model_name": "Random Forest (trees=50, depth=6)",
            "horizon_days": 7
        }
    ]
    with patch("app.services.monitoring_service.query_db", return_value=mock_db_rows), \
         patch("app.services.monitoring_service.reconcile_actual_demand", return_value=0):
        res = get_forecast_monitoring_data(product_id=1, days=30)
        assert res["product_id"] == 1
        assert res["sample_count"] == 1
        assert res["data"][0]["error"] == 2.0  # actual (12) - pred (10)
        assert res["data"][0]["absolute_error"] == 2.0
        assert res["data"][0]["percentage_error"] == 16.67

def test_monitoring_service_summary_computation():
    """Verifies get_monitoring_summary computes correct aggregated metrics."""
    mock_db_rows = [
        {
            "forecast_id": 1,
            "product_id": 1,
            "product_name": "Masala Chai",
            "sku": "SKU-BEV-001",
            "category": "Beverages",
            "forecast_date": "2026-09-01",
            "target_date": "2026-09-02",
            "predicted_demand": 10.0,
            "actual_demand": 14.0,
            "model_name": "Random Forest (trees=50, depth=6)",
            "horizon_days": 7
        },
        {
            "forecast_id": 2,
            "product_id": 1,
            "product_name": "Masala Chai",
            "sku": "SKU-BEV-001",
            "category": "Beverages",
            "forecast_date": "2026-09-01",
            "target_date": "2026-09-03",
            "predicted_demand": 12.0,
            "actual_demand": 10.0,
            "model_name": "Random Forest (trees=50, depth=6)",
            "horizon_days": 7
        }
    ]
    mock_freshness = {
        "last_forecast_date": "2026-09-01",
        "last_actual_date": "2026-09-03"
    }
    with patch("app.services.monitoring_service.query_db", side_effect=[mock_db_rows, mock_freshness]), \
         patch("app.services.monitoring_service.reconcile_actual_demand", return_value=0):
        summary = get_monitoring_summary(product_id=1, days=30)
        assert summary["sample_count"] == 2
        # actuals: 14, 10; preds: 10, 12
        # abs errors: 4, 2 -> MAE = 3.0
        assert summary["metrics"]["mae"] == 3.0
        # Bias: preds (10, 12) - actuals (14, 10) = -4 + 2 = -2 / 2 = -1.0
        assert summary["metrics"]["bias"] == -1.0
        assert "lower than actual demand" in summary["interpretation"]

# ------------------------------------------------------------------------------
# 3. API Route Tests
# ------------------------------------------------------------------------------

def test_api_get_monitoring_forecast(client):
    """Verifies GET /api/monitoring/forecast returns structured 200 payload."""
    mock_payload = {
        "product_id": 1,
        "days": 30,
        "model_name": "Random Forest",
        "sample_count": 1,
        "data": [
            {
                "date": "2026-09-02",
                "predicted_demand": 10.0,
                "actual_demand": 12.0,
                "error": 2.0,
                "absolute_error": 2.0,
                "percentage_error": 16.67,
                "model_name": "Random Forest"
            }
        ]
    }
    with patch("app.routes.monitoring.get_forecast_monitoring_data", return_value=mock_payload):
        res = client.get("/api/monitoring/forecast?product_id=1&days=30")
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert data["product_id"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["error"] == 2.0

def test_api_get_monitoring_summary(client):
    """Verifies GET /api/monitoring/summary returns 200 response with metrics."""
    mock_summary = {
        "product_id": 1,
        "period_days": 30,
        "metrics": {
            "mae": 1.5,
            "rmse": 2.0,
            "wape": 0.1,
            "wape_pct": 10.0,
            "bias": 0.2
        },
        "sample_count": 14,
        "model_name": "Random Forest",
        "interpretation": "Forecasts are, on average, higher than actual demand during the selected period.",
        "data_freshness": {
            "last_forecast_date": "2026-09-20",
            "last_actual_date": "2026-09-20",
            "insufficient_data": False
        }
    }
    with patch("app.routes.monitoring.get_monitoring_summary", return_value=mock_summary):
        res = client.get("/api/monitoring/summary?product_id=1&days=30")
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert data["metrics"]["mae"] == 1.5
        assert data["sample_count"] == 14
        assert "higher than actual demand" in data["interpretation"]

def test_api_reconcile_endpoint(client):
    """Verifies POST /api/monitoring/reconcile triggers reconciliation."""
    with patch("app.routes.monitoring.reconcile_actual_demand", return_value=5):
        res = client.post("/api/monitoring/reconcile", json={"product_id": 1})
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert data["records_updated"] == 5
