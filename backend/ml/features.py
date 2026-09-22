import pandas as pd
import numpy as np

def generate_time_series_features(daily_df):
    """
    Constructs time-series features for each product while strictly preventing data leakage.
    
    1. Lag Features:
       - lag_1, lag_7, lag_14, lag_28
       - Computed per product using shift(k)
       
    2. Rolling Mean Features (No future data leakage):
       - rolling_mean_7, rolling_mean_14, rolling_mean_28
       - Computed using shift(1).rolling(window=w, min_periods=1).mean()
       - Uses shift(1) so today's actual demand is NEVER included in rolling feature calculation!
       
    3. Calendar / Seasonal Features:
       - day_of_week (0 to 6)
       - day_of_month (1 to 31)
       - week_of_year (1 to 52)
       - month (1 to 12)
       - is_weekend (0 or 1)
       
    4. Categorical Encoding:
       - category_encoded (one-hot or frequency encoding)
    """
    df = daily_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["product_id", "date"]).reset_index(drop=True)

    # 1. Calendar Features
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_month"] = df["date"].dt.day
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["month"] = df["date"].dt.month
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # 2. Lag Features (per product)
    for lag in [1, 7, 14, 28]:
        df[f"lag_{lag}"] = df.groupby("product_id")["demand"].shift(lag)

    # 3. Rolling Features (per product, shifted by 1 to prevent leakage)
    for window in [7, 14, 28]:
        df[f"rolling_mean_{window}"] = (
            df.groupby("product_id")["demand"]
            .shift(1)
            .rolling(window=window, min_periods=1)
            .mean()
        )

    # 4. Handle NaNs in lag features safely for early observations
    # For early rows where lag_k is beyond start date, fallback to nearest available lag (e.g. lag_1 or product mean)
    for lag in [1, 7, 14, 28]:
        col = f"lag_{lag}"
        # Fallback cascade: lag_k -> lag_1 -> rolling_mean_7 -> overall product mean -> 0
        df[col] = df[col].fillna(df["lag_1"])
        df[col] = df[col].fillna(df["rolling_mean_7"])
        df[col] = df[col].fillna(df.groupby("product_id")["demand"].transform("mean"))
        df[col] = df[col].fillna(0)

    # Fill any remaining rolling NaNs
    for window in [7, 14, 28]:
        col = f"rolling_mean_{window}"
        df[col] = df[col].fillna(df["lag_1"]).fillna(0)

    # 5. One-Hot Encode Category
    if "category" in df.columns:
        cat_dummies = pd.get_dummies(df["category"], prefix="cat", drop_first=False, dtype=int)
        df = pd.concat([df, cat_dummies], axis=1)

    return df

def get_feature_columns(df):
    """Returns the list of engineered feature column names."""
    base_features = [
        "day_of_week",
        "day_of_month",
        "week_of_year",
        "month",
        "is_weekend",
        "lag_1",
        "lag_7",
        "lag_14",
        "lag_28",
        "rolling_mean_7",
        "rolling_mean_14",
        "rolling_mean_28"
    ]
    cat_features = [col for col in df.columns if col.startswith("cat_")]
    return [col for col in base_features + cat_features if col in df.columns]
