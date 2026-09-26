import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from ml.data_loader import validate_raw_sales_data
from ml.preprocessing import create_daily_product_demand
from ml.features import generate_time_series_features, get_feature_columns
from ml.baselines import NaiveBaseline, MovingAverageBaseline
from ml.models import RidgeDemandModel, RandomForestDemandModel
from ml.evaluation import (
    calculate_mae,
    calculate_rmse,
    calculate_wape,
    calculate_bias,
    evaluate_model_predictions
)
from ml.forecasting import (
    split_time_series_chronological,
    evaluate_candidate_models,
    select_best_model,
    calculate_inventory_business_metrics
)

# ------------------------------------------------------------------------------
# 1. Test Evaluation Metrics
# ------------------------------------------------------------------------------
def test_evaluation_metrics_calculations():
    """Verifies MAE, RMSE, WAPE, and Bias formulas on deterministic arrays."""
    y_true = np.array([10.0, 20.0, 30.0, 40.0])
    y_pred = np.array([12.0, 18.0, 33.0, 35.0])

    # Absolute errors: [2, 2, 3, 5] -> sum = 12, mean = 3.0
    assert calculate_mae(y_true, y_pred) == 3.0

    # Squared errors: [4, 4, 9, 25] -> sum = 42, mean = 10.5 -> sqrt(10.5)
    assert round(calculate_rmse(y_true, y_pred), 4) == round(np.sqrt(10.5), 4)

    # WAPE: sum(|e|) / sum(y) = 12 / 100 = 0.12
    assert calculate_wape(y_true, y_pred) == 0.12

    # Forecast Bias: sum(y_pred - y_true) / N = (2 - 2 + 3 - 5) / 4 = -2 / 4 = -0.5
    assert calculate_bias(y_true, y_pred) == -0.5

def test_wape_zero_actual_demand_protection():
    """Verifies that WAPE handles all-zero actual demand safely without ZeroDivisionError."""
    y_true_zero = np.array([0, 0, 0])
    y_pred_zero = np.array([0, 0, 0])
    assert calculate_wape(y_true_zero, y_pred_zero) == 0.0

    y_pred_non_zero = np.array([1, 2, 0])
    assert calculate_wape(y_true_zero, y_pred_non_zero) is None

# ------------------------------------------------------------------------------
# 2. Test Data Validation
# ------------------------------------------------------------------------------
def test_data_validation_and_cleaning():
    """Verifies that invalid rows, missing IDs, and non-positive quantities are filtered."""
    mock_data = pd.DataFrame([
        {"sale_id": 1, "product_id": 1, "sale_date": "2026-08-20 10:00:00", "quantity": 5},
        {"sale_id": 2, "product_id": None, "sale_date": "2026-08-20 11:00:00", "quantity": 3},  # Missing product_id
        {"sale_id": 3, "product_id": 2, "sale_date": None, "quantity": 4},                       # Missing date
        {"sale_id": 4, "product_id": 2, "sale_date": "2026-08-20 12:00:00", "quantity": -2},     # Negative quantity
        {"sale_id": 5, "product_id": 2, "sale_date": "2026-08-20 13:00:00", "quantity": 0},      # Zero quantity
        {"sale_id": 6, "product_id": 3, "sale_date": "2026-08-21 14:00:00", "quantity": 8}
    ])

    clean_df, report = validate_raw_sales_data(mock_data)
    assert len(clean_df) == 2
    assert set(clean_df["product_id"].unique()) == {1, 3}
    assert report["invalid_quantities"] == 2
    assert report["missing_product_ids"] == 1
    assert report["missing_dates"] == 1
    assert report["dropped_records"] == 4

# ------------------------------------------------------------------------------
# 3. Test Daily Aggregation & Zero-Demand Grid
# ------------------------------------------------------------------------------
def test_daily_demand_aggregation_with_zero_grid():
    """Verifies that daily aggregation creates a continuous Cartesian grid with 0 demand on missing days."""
    mock_raw = pd.DataFrame([
        {"product_id": 1, "sku": "SKU-1", "product_name": "Product 1", "category": "Snacks", "sale_date": "2026-09-01 10:00:00", "quantity": 2},
        {"product_id": 1, "sku": "SKU-1", "product_name": "Product 1", "category": "Snacks", "sale_date": "2026-09-01 15:00:00", "quantity": 3},
        {"product_id": 1, "sku": "SKU-1", "product_name": "Product 1", "category": "Snacks", "sale_date": "2026-09-03 12:00:00", "quantity": 4},
        {"product_id": 2, "sku": "SKU-2", "product_name": "Product 2", "category": "Beverages", "sale_date": "2026-09-02 11:00:00", "quantity": 1}
    ])

    daily_df = create_daily_product_demand(mock_raw)
    
    # 2 products across 3 days (Sept 1, Sept 2, Sept 3) = 6 rows
    assert len(daily_df) == 6

    # Product 1 on Sept 1 should have demand = 2 + 3 = 5
    p1_d1 = daily_df[(daily_df["product_id"] == 1) & (daily_df["date"] == pd.Timestamp("2026-09-01"))]
    assert p1_d1["demand"].values[0] == 5

    # Product 1 on Sept 2 had no sales -> should be 0
    p1_d2 = daily_df[(daily_df["product_id"] == 1) & (daily_df["date"] == pd.Timestamp("2026-09-02"))]
    assert p1_d2["demand"].values[0] == 0

# ------------------------------------------------------------------------------
# 4. Test Feature Engineering & No Data Leakage
# ------------------------------------------------------------------------------
def test_feature_engineering_no_future_leakage():
    """Verifies lag and rolling features are shifted such that today's demand is NEVER leaked."""
    dates = pd.date_range("2026-08-01", periods=10, freq="D")
    daily_df = pd.DataFrame({
        "product_id": [1] * 10,
        "sku": ["SKU-1"] * 10,
        "product_name": ["P1"] * 10,
        "category": ["Snacks"] * 10,
        "date": dates,
        "demand": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    })

    featured_df = generate_time_series_features(daily_df)

    # On day index 2 (date: 2026-08-03, demand: 30):
    # lag_1 MUST be 20 (yesterday)
    assert featured_df.loc[2, "lag_1"] == 20
    # rolling_mean_7 at day index 2 must ONLY average past days [10, 20] -> 15.0, NOT including today's 30!
    assert featured_df.loc[2, "rolling_mean_7"] == 15.0

    # Ensure no NaN remains
    feature_cols = get_feature_columns(featured_df)
    assert featured_df[feature_cols].isna().sum().sum() == 0

# ------------------------------------------------------------------------------
# 5. Test Chronological Splitting
# ------------------------------------------------------------------------------
def test_chronological_time_split():
    """Verifies that time-series data is split strictly chronologically without future leakage."""
    dates = pd.date_range("2026-08-01", periods=20, freq="D")
    df = pd.DataFrame({
        "product_id": [1] * 20,
        "date": dates,
        "demand": np.random.randint(1, 10, 20),
        "lag_1": np.random.randint(1, 10, 20),
        "rolling_mean_7": np.random.randint(1, 10, 20)
    })

    train_df, val_df, test_df, split_info = split_time_series_chronological(
        df, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15
    )

    # Maximum train date must be strictly before minimum val date
    assert train_df["date"].max() < val_df["date"].min()
    # Maximum val date must be strictly before minimum test date
    assert val_df["date"].max() < test_df["date"].min()
    assert split_info["train_days"] == 14
    assert split_info["val_days"] == 3
    assert split_info["test_days"] == 3

# ------------------------------------------------------------------------------
# 6. Test Model Training & Benchmarking
# ------------------------------------------------------------------------------
def test_candidate_models_and_baselines():
    """Verifies that all baseline and candidate models train and predict non-negative outputs."""
    dates = pd.date_range("2026-08-01", periods=30, freq="D")
    df = pd.DataFrame({
        "product_id": [1] * 30,
        "date": dates,
        "demand": [5, 6, 8, 4, 7, 10, 12] * 4 + [6, 7],
        "category": ["Snacks"] * 30
    })

    featured_df = generate_time_series_features(daily_df=df)
    feature_cols = get_feature_columns(featured_df)

    train_df, val_df, test_df, _ = split_time_series_chronological(featured_df, 0.7, 0.15, 0.15)
    trained_models, comparison_df = evaluate_candidate_models(train_df, val_df, feature_cols)

    assert len(trained_models) == 5
    assert set(comparison_df["model_name"].values) == {
        "Naive (Lag-1)",
        "Moving Average (7-Day)",
        "Ridge Regression (alpha=1.0)",
        "Random Forest (trees=50, depth=6)",
        "Gradient Boosting (trees=50, depth=4)"
    }

    best_model, best_metrics = select_best_model(trained_models, comparison_df)
    assert best_model is not None
    assert "mae" in best_metrics
    assert "wape" in best_metrics


    # Verify prediction output shape and non-negativity
    X_test = test_df[feature_cols]
    preds = best_model.predict(X_test)
    assert len(preds) == len(test_df)
    assert (preds >= 0).all()

# ------------------------------------------------------------------------------
# 7. Test Inventory Business Metric Calculations
# ------------------------------------------------------------------------------
def test_inventory_business_metrics():
    """Verifies translation of demand forecasts into inventory coverage and stockout risks."""
    forecast = np.array([5.0, 5.0, 5.0, 5.0, 5.0])  # Avg daily forecast = 5 units
    current_stock = 12                               # Lead time = 3 days (lead demand = 15 units)
    cost = 50.0

    metrics = calculate_inventory_business_metrics(
        actual_demand=[4, 6, 5, 5, 5],
        forecasted_demand=forecast,
        current_stock=current_stock,
        unit_cost=cost,
        lead_time_days=3
    )

    # Days of coverage = 12 / 5.0 = 2.4 days
    assert metrics["days_of_coverage"] == 2.4
    # Stockout risk: current stock (12) < lead time demand (15) -> True
    assert metrics["stockout_risk"] is True
