import numpy as np

def calculate_mae(y_true, y_pred):
    """Mean Absolute Error: (1/N) * SUM(|y_true - y_pred|)"""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return float(np.mean(np.abs(y_true - y_pred)))

def calculate_rmse(y_true, y_pred):
    """Root Mean Squared Error: SQRT((1/N) * SUM((y_true - y_pred)^2))"""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

def calculate_wape(y_true, y_pred):
    """
    Weighted Absolute Percentage Error: SUM(|y_true - y_pred|) / SUM(y_true)
    Safe implementation: returns 0.0 if both sum(y_true) == 0 and errors == 0,
    or None/NaN if sum(y_true) == 0 to avoid division by zero.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    total_actual = float(np.sum(y_true))
    total_abs_error = float(np.sum(np.abs(y_true - y_pred)))

    if total_actual == 0:
        return 0.0 if total_abs_error == 0 else None

    return float(total_abs_error / total_actual)

def calculate_bias(y_true, y_pred):
    """
    Forecast Bias: (1/N) * SUM(y_pred - y_true)
    Positive value indicates systematic over-forecasting (excess stock risk).
    Negative value indicates systematic under-forecasting (stockout risk).
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return float(np.mean(y_pred - y_true))

def evaluate_model_predictions(y_true, y_pred):
    """
    Computes all standard retail demand forecasting metrics:
    - MAE
    - RMSE
    - WAPE (as fraction and percentage)
    - Forecast Bias
    """
    mae = calculate_mae(y_true, y_pred)
    rmse = calculate_rmse(y_true, y_pred)
    wape = calculate_wape(y_true, y_pred)
    bias = calculate_bias(y_true, y_pred)

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "wape": round(wape, 4) if wape is not None else None,
        "wape_pct": round(wape * 100, 2) if wape is not None else None,
        "bias": round(bias, 4)
    }
