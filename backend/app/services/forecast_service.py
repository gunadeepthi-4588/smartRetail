import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.db import query_db, get_db
from ml.features import generate_time_series_features, get_feature_columns

_MODEL_CACHE = None
_METADATA_CACHE = None

def get_model_and_metadata():
    """Loads and caches the trained ML model and metadata from ml/saved_models/."""
    global _MODEL_CACHE, _METADATA_CACHE
    if _MODEL_CACHE is not None and _METADATA_CACHE is not None:
        return _MODEL_CACHE, _METADATA_CACHE

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    saved_dir = os.path.join(base_dir, "ml", "saved_models")
    model_path = os.path.join(saved_dir, "demand_forecast_model.joblib")
    meta_path = os.path.join(saved_dir, "model_metadata.json")

    if not os.path.exists(model_path) or not os.path.exists(meta_path):
        # Trigger training if not yet created
        from ml.train import run_ml_pipeline
        run_ml_pipeline()

    _MODEL_CACHE = joblib.load(model_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        _METADATA_CACHE = json.load(f)

    return _MODEL_CACHE, _METADATA_CACHE


def generate_and_save_forecast(product_id, horizon_days=7):
    """
    Generates multi-step future demand predictions for a product and stores them in MySQL.
    
    1. Validates product existence.
    2. Validates horizon (7 or 30).
    3. Fetches historical sales and constructs daily sequence.
    4. Computes multi-step recursive forecasts for T+1 .. T+horizon.
    5. Deduplication strategy: Replaces any previous forecast for this product and forecast_date.
    6. Stores records in `forecasts` table with actual_demand = NULL.
    """
    if horizon_days not in [7, 30]:
        raise ValueError("Horizon must be either 7 or 30 days.")

    # 1. Validate Product
    prod_sql = "SELECT product_id, sku, name, category, cost_price, selling_price FROM products WHERE product_id = %s"
    product = query_db(prod_sql, (product_id,), one=True)
    if not product:
        raise ValueError(f"Product ID {product_id} does not exist.")

    # 2. Fetch Historical Sales
    sales_sql = """
        SELECT 
            DATE(s.sale_date) AS sale_date_str,
            COALESCE(SUM(si.quantity), 0) AS daily_quantity
        FROM sales s
        JOIN sale_items si ON s.sale_id = si.sale_id
        WHERE si.product_id = %s
        GROUP BY DATE(s.sale_date)
        ORDER BY sale_date_str ASC
    """
    sales_rows = query_db(sales_sql, (product_id,))

    # Find system date boundaries
    all_dates_sql = "SELECT MIN(DATE(sale_date)) AS min_date, MAX(DATE(sale_date)) AS max_date FROM sales"
    date_bounds = query_db(all_dates_sql, one=True)
    
    if not date_bounds or not date_bounds["max_date"]:
        min_date = datetime.now().date() - timedelta(days=30)
        max_date = datetime.now().date()
    else:
        min_date = pd.to_datetime(date_bounds["min_date"]).date()
        max_date = pd.to_datetime(date_bounds["max_date"]).date()

    full_date_range = pd.date_range(start=min_date, end=max_date, freq="D")
    df_grid = pd.DataFrame({"date": full_date_range})
    df_grid["product_id"] = product_id
    df_grid["sku"] = product["sku"]
    df_grid["product_name"] = product["name"]
    df_grid["category"] = product["category"]

    if sales_rows:
        df_sales = pd.DataFrame(sales_rows)
        df_sales["date"] = pd.to_datetime(df_sales["sale_date_str"])
        df_sales["demand"] = df_sales["daily_quantity"].astype(int)
        df_hist = pd.merge(df_grid, df_sales[["date", "demand"]], on="date", how="left").fillna(0)
    else:
        df_hist = df_grid.copy()
        df_hist["demand"] = 0

    df_hist["demand"] = df_hist["demand"].astype(int)

    # 3. Load Model Artifact
    model, metadata = get_model_and_metadata()
    feature_cols = metadata["features"]

    # 4. Multi-Step Recursive Forecasting
    current_series = df_hist.copy()
    predictions = []
    forecast_run_date = max_date.strftime("%Y-%m-%d")

    for step in range(1, horizon_days + 1):
        target_date = max_date + timedelta(days=step)
        
        # Add placeholder row for target date
        new_row = pd.DataFrame([{
            "product_id": product_id,
            "sku": product["sku"],
            "product_name": product["name"],
            "category": product["category"],
            "date": pd.Timestamp(target_date),
            "demand": 0 # to be predicted
        }])

        combined = pd.concat([current_series, new_row], ignore_index=True)
        featured = generate_time_series_features(combined)

        # Align columns
        for col in feature_cols:
            if col not in featured.columns:
                featured[col] = 0

        target_row = featured[featured["date"] == pd.Timestamp(target_date)].iloc[0]
        X_step = target_row[feature_cols].values.reshape(1, -1)

        pred_val = float(model.predict(X_step)[0])
        pred_val = max(0.0, round(pred_val, 2))

        # Update combined with predicted value for recursive feature calculation
        current_series = combined.copy()
        current_series.loc[current_series["date"] == pd.Timestamp(target_date), "demand"] = int(round(pred_val))

        predictions.append({
            "target_date": target_date.strftime("%Y-%m-%d"),
            "predicted_demand": pred_val,
            "day_of_week": target_date.strftime("%A")
        })

    # 5. Persist Predictions to Database
    db = get_db()
    cursor = db.cursor()

    # Deduplication strategy: Remove existing forecast run for (product_id, forecast_date, horizon_days)
    del_sql = """
        DELETE FROM forecasts 
        WHERE product_id = %s AND forecast_date = %s AND horizon_days = %s
    """
    cursor.execute(del_sql, (product_id, forecast_run_date, horizon_days))

    # Insert fresh predictions
    ins_sql = """
        INSERT INTO forecasts (product_id, forecast_date, target_date, predicted_demand, actual_demand, model_name, horizon_days)
        VALUES (%s, %s, %s, %s, NULL, %s, %s)
    """
    for p in predictions:
        cursor.execute(ins_sql, (
            product_id,
            forecast_run_date,
            p["target_date"],
            p["predicted_demand"],
            metadata["selected_model_name"],
            horizon_days
        ))

    db.commit()

    total_projected_demand = sum(p["predicted_demand"] for p in predictions)
    avg_daily_demand = round(total_projected_demand / horizon_days, 2)

    return {
        "product": {
            "product_id": product["product_id"],
            "sku": product["sku"],
            "name": product["name"],
            "category": product["category"]
        },
        "forecast_run_date": forecast_run_date,
        "horizon_days": horizon_days,
        "model_name": metadata["selected_model_name"],
        "total_projected_demand": round(total_projected_demand, 2),
        "avg_daily_projected_demand": avg_daily_demand,
        "predictions": predictions
    }


def get_stored_forecasts(product_id=None, horizon_days=None, limit=100):
    """Retrieves stored forecast records from MySQL."""
    conditions = []
    params = []

    if product_id:
        conditions.append("f.product_id = %s")
        params.append(product_id)
    if horizon_days:
        conditions.append("f.horizon_days = %s")
        params.append(horizon_days)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
        SELECT 
            f.forecast_id,
            f.product_id,
            p.name AS product_name,
            p.sku,
            p.category,
            f.forecast_date,
            f.target_date,
            f.predicted_demand,
            f.actual_demand,
            f.model_name,
            f.horizon_days,
            f.created_at
        FROM forecasts f
        JOIN products p ON f.product_id = p.product_id
        {where_clause}
        ORDER BY f.forecast_date DESC, f.target_date ASC
        LIMIT %s
    """
    params.append(limit)
    rows = query_db(sql, tuple(params))

    forecasts = []
    for r in rows:
        forecasts.append({
            "forecast_id": r["forecast_id"],
            "product_id": r["product_id"],
            "product_name": r["product_name"],
            "sku": r["sku"],
            "category": r["category"],
            "forecast_date": r["forecast_date"].strftime("%Y-%m-%d") if hasattr(r["forecast_date"], "strftime") else str(r["forecast_date"]),
            "target_date": r["target_date"].strftime("%Y-%m-%d") if hasattr(r["target_date"], "strftime") else str(r["target_date"]),
            "predicted_demand": float(r["predicted_demand"]),
            "actual_demand": float(r["actual_demand"]) if r["actual_demand"] is not None else None,
            "model_name": r["model_name"],
            "horizon_days": int(r["horizon_days"]),
            "created_at": r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if hasattr(r["created_at"], "strftime") else str(r["created_at"])
        })

    return forecasts


def get_product_forecast_and_history(product_id, horizon_days=7):
    """
    Returns the latest stored forecast alongside historical actual sales for Chart.js rendering:
    - product info
    - historical daily sales (last 14 days)
    - latest future predictions (next 7 or 30 days)
    """
    # 1. Product info
    product = query_db("SELECT product_id, sku, name, category, cost_price, selling_price FROM products WHERE product_id = %s", (product_id,), one=True)
    if not product:
        raise ValueError(f"Product ID {product_id} not found.")

    # 2. Latest Forecast
    forecast_sql = """
        SELECT 
            forecast_id,
            forecast_date,
            target_date,
            predicted_demand,
            actual_demand,
            model_name,
            horizon_days
        FROM forecasts
        WHERE product_id = %s AND horizon_days = %s
        ORDER BY forecast_date DESC, target_date ASC
        LIMIT %s
    """
    forecast_rows = query_db(forecast_sql, (product_id, horizon_days, horizon_days))

    predictions = []
    model_name = "Random Forest (trees=50, depth=6)"
    forecast_date = None

    if forecast_rows:
        forecast_date = forecast_rows[0]["forecast_date"].strftime("%Y-%m-%d") if hasattr(forecast_rows[0]["forecast_date"], "strftime") else str(forecast_rows[0]["forecast_date"])
        model_name = forecast_rows[0]["model_name"]
        for r in forecast_rows:
            predictions.append({
                "target_date": r["target_date"].strftime("%Y-%m-%d") if hasattr(r["target_date"], "strftime") else str(r["target_date"]),
                "predicted_demand": float(r["predicted_demand"]),
                "actual_demand": float(r["actual_demand"]) if r["actual_demand"] is not None else None
            })

    # 3. Recent Historical Actual Sales (Last 14 days)
    hist_sql = """
        SELECT 
            DATE(s.sale_date) AS sale_date_str,
            COALESCE(SUM(si.quantity), 0) AS actual_units
        FROM sales s
        JOIN sale_items si ON s.sale_id = si.sale_id
        WHERE si.product_id = %s
        GROUP BY DATE(s.sale_date)
        ORDER BY sale_date_str DESC
        LIMIT 14
    """
    hist_rows = query_db(hist_sql, (product_id,))
    
    history = []
    for hr in reversed(hist_rows or []):
        history.append({
            "date": hr["sale_date_str"].strftime("%Y-%m-%d") if hasattr(hr["sale_date_str"], "strftime") else str(hr["sale_date_str"]),
            "actual_demand": int(hr["actual_units"])
        })

    return {
        "product": {
            "product_id": product["product_id"],
            "sku": product["sku"],
            "name": product["name"],
            "category": product["category"]
        },
        "has_forecast": len(predictions) > 0,
        "forecast_run_date": forecast_date,
        "model_name": model_name,
        "horizon_days": horizon_days,
        "history": history,
        "predictions": predictions
    }


def update_actual_demand_if_available():
    """
    Helper to update actual_demand in the forecasts table for past target dates
    where actual sales have occurred.
    """
    db = get_db()
    cursor = db.cursor()

    sql = """
        UPDATE forecasts f
        JOIN (
            SELECT 
                si.product_id,
                DATE(s.sale_date) AS actual_date,
                SUM(si.quantity) AS total_actual_sold
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            GROUP BY si.product_id, DATE(s.sale_date)
        ) actuals ON f.product_id = actuals.product_id AND f.target_date = actuals.actual_date
        SET f.actual_demand = actuals.total_actual_sold
        WHERE f.actual_demand IS NULL AND f.target_date <= CURDATE()
    """
    cursor.execute(sql)
    affected = cursor.rowcount
    db.commit()
    return affected
