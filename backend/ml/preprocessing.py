import pandas as pd
import numpy as np

def create_daily_product_demand(df):
    """
    Transforms raw transaction items into a daily product-level time-series grid.
    
    1. Truncates timestamps to daily dates (YYYY-MM-DD).
    2. Sums quantity sold per product per date: demand = SUM(quantity).
    3. Reconstructs a continuous daily date grid for every product between min_date and max_date.
    4. Fills zero-sales days with demand = 0 to capture intermittent retail demand.
    """
    # 1. Truncate timestamp to date
    df = df.copy()
    df["date"] = pd.to_datetime(df["sale_date"]).dt.normalize()

    # 2. Daily aggregation: demand per product per date
    daily_agg = df.groupby(["product_id", "date"])["quantity"].sum().reset_index()
    daily_agg.rename(columns={"quantity": "demand"}, inplace=True)

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
    merged["demand"] = merged["demand"].fillna(0).astype(int)

    # Re-attach product metadata
    merged = pd.merge(merged, prod_meta, on="product_id", how="left")
    
    # Sort chronologically per product
    merged = merged.sort_values(by=["product_id", "date"]).reset_index(drop=True)

    return merged
