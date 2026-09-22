import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime

from ml.data_loader import get_raw_sales_data
from ml.preprocessing import create_daily_product_demand
from ml.features import generate_time_series_features, get_feature_columns
from ml.forecasting import (
    split_time_series_chronological,
    evaluate_candidate_models,
    select_best_model
)
from ml.evaluation import evaluate_model_predictions

def run_ml_pipeline():
    """
    Executes the end-to-end SmartRetail Demand Forecasting Pipeline:
    1. Extract & validate historical transactions.
    2. Aggregate daily demand on a continuous product-date grid.
    3. Generate time-series features (Lags, Rolling means, Seasonality).
    4. Chronological Train / Validation / Test split.
    5. Benchmark Baselines vs Ridge vs Random Forest.
    6. Select the optimal model.
    7. Evaluate on held-out test set.
    8. Persist model artifact & metadata for Phase 11 API consumption.
    """
    print("=" * 70)
    print(" SmartRetail — Demand Forecasting ML Pipeline")
    print("=" * 70)

    # 1. Load & Validate Raw Data
    print("\n[Step 1/7] Extracting & Validating Sales Transactions...")
    raw_df, quality_report = get_raw_sales_data()
    print(f" -> Total Raw Records: {quality_report['total_raw_records']}")
    print(f" -> Valid Transactions: {quality_report['valid_records_count']}")
    print(f" -> Unique Products: {quality_report['unique_products_count']}")
    print(f" -> Historical Date Span: {quality_report['date_range_start']} to {quality_report['date_range_end']}")
    print(f" -> Quality Status: {quality_report['status']}")

    # 2. Daily Product-Level Aggregation with Zero-Sales Grid
    print("\n[Step 2/7] Aggregating Daily Product Demand Grid...")
    daily_df = create_daily_product_demand(raw_df)
    print(f" -> Total Product-Day Observations: {len(daily_df)}")
    print(f" -> Total Units Sold: {daily_df['demand'].sum():,}")
    print(f" -> Zero-Sales Grid Days: {(daily_df['demand'] == 0).sum():,} observations")

    # 3. Feature Engineering (Strictly No Future Leakage)
    print("\n[Step 3/7] Engineering Time-Series Lag & Rolling Features...")
    featured_df = generate_time_series_features(daily_df)
    feature_cols = get_feature_columns(featured_df)
    print(f" -> Total Engineered Features: {len(feature_cols)}")
    print(f" -> Features: {', '.join(feature_cols)}")

    # 4. Chronological Train / Val / Test Split
    print("\n[Step 4/7] Splitting Data Chronologically (No Random Shuffling)...")
    train_df, val_df, test_df, split_info = split_time_series_chronological(
        featured_df, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15
    )
    print(f" -> Training Period   : {split_info['train_start']} to {split_info['train_end']} ({split_info['train_days']} days, {len(train_df)} rows)")
    print(f" -> Validation Period : {split_info['val_start']} to {split_info['val_end']} ({split_info['val_days']} days, {len(val_df)} rows)")
    print(f" -> Test Period       : {split_info['test_start']} to {split_info['test_end']} ({split_info['test_days']} days, {len(test_df)} rows)")

    # 5. Model Training & Validation Benchmarking
    print("\n[Step 5/7] Training Baseline & Candidate ML Models...")
    trained_models, comparison_df = evaluate_candidate_models(train_df, val_df, feature_cols)

    print("\n" + "-" * 70)
    print(" MODEL VALIDATION PERFORMANCE COMPARISON")
    print("-" * 70)
    print(f"{'Model':<35} | {'MAE':<7} | {'RMSE':<7} | {'WAPE %':<8} | {'Bias':<7}")
    print("-" * 70)
    for _, row in comparison_df.iterrows():
        wape_str = f"{row['wape_pct']}%" if row['wape_pct'] is not None else "N/A"
        print(f"{row['model_name']:<35} | {row['mae']:<7.4f} | {row['rmse']:<7.4f} | {wape_str:<8} | {row['bias']:<7.4f}")
    print("-" * 70)

    # 6. Model Selection
    print("\n[Step 6/7] Selecting Best Performing Model...")
    best_model, best_metrics = select_best_model(trained_models, comparison_df)
    print(f" -> Selected Model: {best_model.name}")
    print(f" -> Validation WAPE: {best_metrics['wape_pct']}% | MAE: {best_metrics['mae']}")

    # 7. Held-out Test Evaluation
    X_test = test_df[feature_cols]
    y_test = test_df["demand"].values
    test_preds = best_model.predict(X_test)
    test_metrics = evaluate_model_predictions(y_test, test_preds)
    print(f" -> Held-Out Test WAPE: {test_metrics['wape_pct']}% | Test MAE: {test_metrics['mae']} | Test Bias: {test_metrics['bias']}")

    # 8. Persist Artifacts
    print("\n[Step 7/7] Persisting Model Artifacts...")
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_models")
    os.makedirs(save_dir, exist_ok=True)

    model_path = os.path.join(save_dir, "demand_forecast_model.joblib")
    joblib.dump(best_model, model_path)
    print(f" -> Model Saved: {model_path}")

    metadata = {
        "selected_model_name": best_model.name,
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "features": feature_cols,
        "data_quality": quality_report,
        "split_info": split_info,
        "validation_metrics": best_metrics,
        "test_metrics": test_metrics,
        "model_comparison": comparison_df.to_dict(orient="records")
    }

    metadata_path = os.path.join(save_dir, "model_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f" -> Metadata Saved: {metadata_path}")

    print("\n" + "=" * 70)
    print(" ML Demand Forecasting Pipeline Successfully Completed!")
    print("=" * 70)

    return metadata

if __name__ == "__main__":
    run_ml_pipeline()
