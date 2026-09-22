"""
Forecast Monitoring & Model Performance Service
Calculates accuracy metrics (MAE, RMSE, WAPE, Bias) comparing predicted demand against actual sales.
Does NOT perform model retraining or automatic replacement.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from app.db import query_db, get_db

def reconcile_actual_demand(product_id=None):
    """
    Safely synchronizes `actual_demand` in the `forecasts` table with historical sales data.
    Populates actual_demand for target dates where sales have occurred and actual_demand is currently NULL.
    Does NOT modify sales or overwrite valid actuals.
    """
    db = get_db()
    cursor = db.cursor()

    prod_filter = "AND f.product_id = %s" if product_id else ""
    params = (product_id,) if product_id else ()

    sql = f"""
        UPDATE forecasts f
        JOIN (
            SELECT 
                si.product_id,
                DATE(s.sale_date) AS actual_date,
                COALESCE(SUM(si.quantity), 0) AS total_actual_sold
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            GROUP BY si.product_id, DATE(s.sale_date)
        ) actuals ON f.product_id = actuals.product_id AND f.target_date = actuals.actual_date
        SET f.actual_demand = actuals.total_actual_sold
        WHERE f.actual_demand IS NULL 
          AND f.target_date <= (SELECT MAX(DATE(sale_date)) FROM sales)
          {prod_filter}
    """
    cursor.execute(sql, params)
    updated_rows = cursor.rowcount
    db.commit()
    return updated_rows


def calculate_metrics_from_arrays(y_true, y_pred):
    """
    Computes standard evaluation metrics from numpy/list arrays:
    - MAE  = mean(|actual - predicted|)
    - RMSE = sqrt(mean((actual - predicted)^2))
    - WAPE = sum(|actual - predicted|) / sum(actual) [when sum(actual) > 0]
    - Bias = mean(predicted - actual) [Positive: over-prediction, Negative: under-prediction]
    """
    if y_true is None or y_pred is None or len(y_true) == 0 or len(y_pred) == 0:
        return {
            "mae": None,
            "rmse": None,
            "wape": None,
            "wape_pct": None,
            "bias": None,
            "sample_count": 0
        }

    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    n = len(y_true)
    if n == 0:
        return {
            "mae": None,
            "rmse": None,
            "wape": None,
            "wape_pct": None,
            "bias": None,
            "sample_count": 0
        }

    abs_errors = np.abs(y_true - y_pred)
    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    total_actual = float(np.sum(y_true))
    total_abs_error = float(np.sum(abs_errors))

    if total_actual > 0:
        wape = float(total_abs_error / total_actual)
        wape_pct = round(wape * 100, 2)
    else:
        wape = 0.0 if total_abs_error == 0 else None
        wape_pct = 0.0 if total_abs_error == 0 else None

    # Bias: mean(predicted - actual)
    bias = float(np.mean(y_pred - y_true))

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "wape": round(wape, 4) if wape is not None else None,
        "wape_pct": wape_pct,
        "bias": round(bias, 4),
        "sample_count": n
    }


def get_deterministic_interpretation(bias, sample_count):
    """
    Returns a neutral, deterministic interpretation based on the computed forecast bias.
    Does not label models as 'good' or 'bad'.
    """
    if sample_count == 0:
        return "Insufficient historical actual data available for this evaluation window."
    
    if bias is None:
        return "Unable to compute forecast bias for the selected period."

    if bias > 0.05:
        return "Forecasts are, on average, higher than actual demand during the selected period."
    elif bias < -0.05:
        return "Forecasts are, on average, lower than actual demand during the selected period."
    else:
        return "Forecasts are close to actual demand on average, based on the selected period."


def get_forecast_monitoring_data(product_id=None, days=30, model_name=None):
    """
    Fetches historical forecast records with matching actual sales demand.
    Returns array of structured records with predicted, actual, error, absolute_error.
    """
    # Safe auto-reconcile of actuals
    try:
        reconcile_actual_demand(product_id=product_id)
    except Exception:
        pass

    # Normalize days
    try:
        days = int(days)
        if days not in [7, 30, 90]:
            days = 30
    except (ValueError, TypeError):
        days = 30

    conditions = ["f.actual_demand IS NOT NULL"]
    params = []

    if product_id:
        conditions.append("f.product_id = %s")
        params.append(product_id)

    if model_name:
        conditions.append("f.model_name = %s")
        params.append(model_name)

    # Date boundary filter: target dates within the latest N days
    # Using dataset max target date or current date
    conditions.append(f"f.target_date >= (SELECT COALESCE(MAX(target_date), CURDATE()) FROM forecasts WHERE actual_demand IS NOT NULL) - INTERVAL %s DAY")
    params.append(days)

    where_clause = f"WHERE {' AND '.join(conditions)}"

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
            f.horizon_days
        FROM forecasts f
        JOIN products p ON f.product_id = p.product_id
        {where_clause}
        ORDER BY f.target_date ASC, f.product_id ASC
    """

    rows = query_db(sql, tuple(params))

    records = []
    models_seen = set()

    for r in rows:
        pred = float(r["predicted_demand"])
        act = float(r["actual_demand"])
        err = round(act - pred, 2)
        abs_err = round(abs(act - pred), 2)
        pct_err = round((abs_err / act) * 100, 2) if act > 0 else None

        t_date_str = r["target_date"].strftime("%Y-%m-%d") if hasattr(r["target_date"], "strftime") else str(r["target_date"])
        f_date_str = r["forecast_date"].strftime("%Y-%m-%d") if hasattr(r["forecast_date"], "strftime") else str(r["forecast_date"])

        if r["model_name"]:
            models_seen.add(r["model_name"])

        records.append({
            "forecast_id": r["forecast_id"],
            "product_id": r["product_id"],
            "product_name": r["product_name"],
            "sku": r["sku"],
            "category": r["category"],
            "date": t_date_str,
            "target_date": t_date_str,
            "forecast_date": f_date_str,
            "predicted_demand": pred,
            "actual_demand": act,
            "error": err,
            "absolute_error": abs_err,
            "percentage_error": pct_err,
            "model_name": r["model_name"],
            "horizon_days": int(r["horizon_days"])
        })

    primary_model = list(models_seen)[0] if models_seen else "Random Forest (trees=50, depth=6)"

    return {
        "product_id": int(product_id) if product_id else None,
        "days": days,
        "model_name": primary_model,
        "sample_count": len(records),
        "data": records
    }


def get_monitoring_summary(product_id=None, days=30, model_name=None):
    """
    Computes aggregate accuracy metrics, bias, and metadata for the requested product and window.
    """
    monitoring_result = get_forecast_monitoring_data(product_id=product_id, days=days, model_name=model_name)
    records = monitoring_result["data"]

    # Freshness queries
    freshness_sql = """
        SELECT 
            MAX(forecast_date) AS last_forecast_date,
            MAX(CASE WHEN actual_demand IS NOT NULL THEN target_date ELSE NULL END) AS last_actual_date
        FROM forecasts
        WHERE (%s IS NULL OR product_id = %s)
    """
    freshness_row = query_db(freshness_sql, (product_id, product_id), one=True)
    
    last_forecast_str = None
    last_actual_str = None
    if freshness_row:
        if freshness_row["last_forecast_date"]:
            last_forecast_str = freshness_row["last_forecast_date"].strftime("%Y-%m-%d") if hasattr(freshness_row["last_forecast_date"], "strftime") else str(freshness_row["last_forecast_date"])
        if freshness_row["last_actual_date"]:
            last_actual_str = freshness_row["last_actual_date"].strftime("%Y-%m-%d") if hasattr(freshness_row["last_actual_date"], "strftime") else str(freshness_row["last_actual_date"])

    if not records:
        return {
            "product_id": int(product_id) if product_id else None,
            "period_days": days,
            "metrics": {
                "mae": None,
                "rmse": None,
                "wape": None,
                "wape_pct": None,
                "bias": None
            },
            "sample_count": 0,
            "model_name": monitoring_result.get("model_name", "Random Forest (trees=50, depth=6)"),
            "interpretation": "Insufficient historical actual data available for this evaluation window.",
            "data_freshness": {
                "last_forecast_date": last_forecast_str,
                "last_actual_date": last_actual_str,
                "insufficient_data": True,
                "message": "Actual sales data is not yet available for this forecast period."
            }
        }

    y_true = [r["actual_demand"] for r in records]
    y_pred = [r["predicted_demand"] for r in records]

    metrics = calculate_metrics_from_arrays(y_true, y_pred)
    interpretation = get_deterministic_interpretation(metrics["bias"], metrics["sample_count"])

    return {
        "product_id": int(product_id) if product_id else None,
        "period_days": days,
        "metrics": {
            "mae": metrics["mae"],
            "rmse": metrics["rmse"],
            "wape": metrics["wape"],
            "wape_pct": metrics["wape_pct"],
            "bias": metrics["bias"]
        },
        "sample_count": metrics["sample_count"],
        "model_name": monitoring_result["model_name"],
        "interpretation": interpretation,
        "data_freshness": {
            "last_forecast_date": last_forecast_str,
            "last_actual_date": last_actual_str,
            "insufficient_data": False,
            "message": "Monitoring data is up-to-date."
        }
    }
