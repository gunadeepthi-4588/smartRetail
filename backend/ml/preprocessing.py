import os
import json
import pandas as pd
import numpy as np

def create_daily_product_demand(df, stockout_annotations_path=None):
    """
    Transforms raw transaction items into a daily product-level time-series grid
    and explicitly handles stockout-affected censored demand.
    
    1. Truncates timestamps to daily dates (YYYY-MM-DD).
    2. Sums quantity sold per product per date: observed_demand = SUM(quantity).
    3. Reconstructs a continuous daily date grid for every product between min_date and max_date.
    4. Fills zero-sales days with observed_demand = 0.
    5. Applies stockout censoring adjustment when stockout annotations are present:
       - Censored rate scaling: unconstrained_demand = observed_demand * (16 / in_stock_hours)
       - Full-day stockout imputation from recent 7-day rolling uncensored mean.
    """
    # 1. Truncate timestamp to date
    df = df.copy()
    df["date"] = pd.to_datetime(df["sale_date"]).dt.normalize()

    # 2. Daily aggregation: demand per product per date
    daily_agg = df.groupby(["product_id", "date"])["quantity"].sum().reset_index()
    daily_agg.rename(columns={"quantity": "observed_demand"}, inplace=True)

    # Fetch product metadata (sku, name, category) for joining back
    prod_meta = df[["product_id", "sku", "product_name", "category"]].drop_duplicates(subset=["product_id"])

    # 3. Create full Cartesian product of (unique products x continuous date range)
    all_products = prod_meta["product_id"].unique()
    min_date = daily_agg["date"].min()
    max_date = daily_agg["date"].max()

    full_date_range = pd.date_range(start=min_date, end=max_date, freq="D")
    
    # MultiIndex grid
    grid_index = pd.MultiIndex.from_product(
        [all_products, full_date_range],
        names=["product_id", "date"]
    ).to_frame().reset_index(drop=True)

    # 4. Merge aggregated sales onto the continuous grid and fill 0s
    merged = pd.merge(grid_index, daily_agg, on=["product_id", "date"], how="left")
    merged["observed_demand"] = merged["observed_demand"].fillna(0).astype(int)

    # 5. Stockout Annotation Integration & Censoring Correction
    if stockout_annotations_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        stockout_annotations_path = os.path.join(base_dir, "saved_models", "stockout_annotations.json")

    stockout_dict = {}
    if os.path.exists(stockout_annotations_path):
        try:
            with open(stockout_annotations_path, "r", encoding="utf-8") as f:
                stockout_dict = json.load(f)
        except Exception:
            pass

    # Match annotations by product_id and date
    merged["date_str"] = merged["date"].dt.strftime("%Y-%m-%d")
    merged["key"] = merged["product_id"].astype(str) + "_" + merged["date_str"]

    if stockout_dict:
        merged["stockout_hours"] = merged["key"].map(lambda k: stockout_dict.get(k, {}).get("stockout_hours", 0))
        merged["in_stock_hours"] = merged["key"].map(lambda k: stockout_dict.get(k, {}).get("in_stock_hours", 16))
        merged["is_stockout"] = merged["key"].map(lambda k: stockout_dict.get(k, {}).get("is_stockout", 0))
    else:
        merged["stockout_hours"] = 0
        merged["in_stock_hours"] = 16
        merged["is_stockout"] = 0

    # Calculate unconstrained target demand
    merged["demand"] = merged["observed_demand"].copy().astype(float)
    
    # Scale partially censored days:
    partial_so = (merged["stockout_hours"] > 0) & (merged["stockout_hours"] < 16)
    merged.loc[partial_so, "demand"] = (
        merged.loc[partial_so, "observed_demand"] * (16.0 / merged.loc[partial_so, "in_stock_hours"])
    )

    # Reconstruct fully stocked out days (16 hours out of stock) using 7-day rolling uncensored mean per product
    for pid in all_products:
        pmask = merged["product_id"] == pid
        full_so_mask = pmask & (merged["stockout_hours"] >= 16)
        if full_so_mask.any():
            rolling_rec = merged.loc[pmask, "demand"].rolling(7, min_periods=1).mean()
            merged.loc[full_so_mask, "demand"] = rolling_rec[full_so_mask]

    merged["demand"] = merged["demand"].round().astype(int)

    # Clean temporary helper columns
    merged.drop(columns=["date_str", "key"], inplace=True)

    # Re-attach product metadata
    merged = pd.merge(merged, prod_meta, on="product_id", how="left")
    
    # Sort chronologically per product
    merged = merged.sort_values(by=["product_id", "date"]).reset_index(drop=True)

    return merged
