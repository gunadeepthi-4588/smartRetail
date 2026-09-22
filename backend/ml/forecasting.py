import pandas as pd
import numpy as np
from datetime import timedelta
from ml.baselines import NaiveBaseline, MovingAverageBaseline
from ml.models import RidgeDemandModel, RandomForestDemandModel
from ml.evaluation import evaluate_model_predictions

def split_time_series_chronological(df, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15):
    """
    Splits the continuous multi-product time-series dataset strictly chronologically.
    
    1. Extracts unique sorted dates across the dataset.
    2. Computes index cuts for train, validation, and test periods.
    3. Partitions data based on date boundaries to prevent any future information leakage.
    """
    unique_dates = np.sort(df["date"].unique())
    n_dates = len(unique_dates)

    if n_dates < 5:
        raise ValueError(f"Insufficient time steps for time-series splitting: only {n_dates} distinct dates found.")

    train_end_idx = int(n_dates * train_ratio)
    val_end_idx = int(n_dates * (train_ratio + val_ratio))

    # Guard against empty partitions
    if train_end_idx == 0:
        train_end_idx = 1
    if val_end_idx <= train_end_idx:
        val_end_idx = train_end_idx + 1

    train_dates = unique_dates[:train_end_idx]
    val_dates = unique_dates[train_end_idx:val_end_idx]
    test_dates = unique_dates[val_end_idx:]

    train_df = df[df["date"].isin(train_dates)].copy()
    val_df = df[df["date"].isin(val_dates)].copy()
    test_df = df[df["date"].isin(test_dates)].copy()

    split_info = {
        "total_days": n_dates,
        "train_days": len(train_dates),
        "train_start": pd.to_datetime(train_dates[0]).strftime("%Y-%m-%d"),
        "train_end": pd.to_datetime(train_dates[-1]).strftime("%Y-%m-%d"),
        "val_days": len(val_dates),
        "val_start": pd.to_datetime(val_dates[0]).strftime("%Y-%m-%d"),
        "val_end": pd.to_datetime(val_dates[-1]).strftime("%Y-%m-%d"),
        "test_days": len(test_dates),
        "test_start": pd.to_datetime(test_dates[0]).strftime("%Y-%m-%d") if len(test_dates) > 0 else "N/A",
        "test_end": pd.to_datetime(test_dates[-1]).strftime("%Y-%m-%d") if len(test_dates) > 0 else "N/A",
    }

    return train_df, val_df, test_df, split_info

def evaluate_candidate_models(train_df, val_df, feature_cols):
    """
    Trains and benchmarks candidate models on the chronological validation set:
    1. Naive (Lag-1) Baseline
    2. Moving Average (7-Day) Baseline
    3. Ridge Regression (L2 Linear)
    4. Random Forest Regressor
    
    Returns a dictionary of trained models and a comparison leaderboard.
    """
    X_train = train_df[feature_cols]
    y_train = train_df["demand"].values

    X_val = val_df[feature_cols]
    y_val = val_df["demand"].values

    candidates = [
        NaiveBaseline(),
        MovingAverageBaseline(window=7),
        RidgeDemandModel(alpha=1.0),
        RandomForestDemandModel(n_estimators=50, max_depth=6, random_state=42)
    ]

    results = []
    trained_models = {}

    for model in candidates:
        # Fit model
        model.fit(X_train, y_train)
        trained_models[model.name] = model

        # Predict on validation set
        val_preds = model.predict(X_val)

        # Evaluate performance
        metrics = evaluate_model_predictions(y_val, val_preds)
        metrics["model_name"] = model.name
        results.append(metrics)

    comparison_df = pd.DataFrame(results)
    # Sort by WAPE ascending (or MAE if WAPE is tied)
    comparison_df = comparison_df.sort_values(by=["wape", "mae"]).reset_index(drop=True)

    return trained_models, comparison_df

def select_best_model(trained_models, comparison_df):
    """Selects the winning model based on lowest validation WAPE / MAE."""
    best_row = comparison_df.iloc[0]
    best_model_name = best_row["model_name"]
    best_model = trained_models[best_model_name]
    return best_model, best_row.to_dict()

def calculate_inventory_business_metrics(actual_demand, forecasted_demand, current_stock, unit_cost, lead_time_days=3):
    """
    Translates forecasting accuracy into actionable inventory business metrics:
    - Days of coverage: current_stock / avg_daily_forecast
    - Stockout risk: whether forecasted demand over lead time exceeds current stock
    - Overstock valuation: excess stock value beyond 30-day forecasted demand
    """
    avg_daily_forecast = max(0.01, float(np.mean(forecasted_demand)))
    days_of_coverage = round(current_stock / avg_daily_forecast, 1)

    lead_time_demand = avg_daily_forecast * lead_time_days
    stockout_risk = current_stock < lead_time_demand

    demand_30d = avg_daily_forecast * 30
    excess_units = max(0, current_stock - (demand_30d * 1.5))
    overstock_holding_value = round(excess_units * unit_cost, 2)

    return {
        "days_of_coverage": days_of_coverage,
        "lead_time_demand": round(lead_time_demand, 1),
        "stockout_risk": stockout_risk,
        "excess_units": int(excess_units),
        "overstock_holding_value": overstock_holding_value
    }
