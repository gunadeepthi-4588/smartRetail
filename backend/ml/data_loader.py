import re
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import os

def load_sales_from_mysql():
    """Attempts to query the live MySQL database via Flask app context."""
    try:
        from app import create_app
        from app.db import query_db
        app = create_app()
        with app.app_context():
            sql = """
                SELECT 
                    s.sale_id,
                    s.sale_date,
                    s.receipt_number,
                    s.payment_method,
                    si.sale_item_id,
                    si.product_id,
                    p.sku,
                    p.name AS product_name,
                    p.category,
                    si.quantity,
                    si.unit_price,
                    si.unit_cost
                FROM sales s
                JOIN sale_items si ON s.sale_id = si.sale_id
                JOIN products p ON si.product_id = p.product_id
                ORDER BY s.sale_date ASC
            """
            rows = query_db(sql)
            if rows:
                return pd.DataFrame(rows)
    except Exception as e:
        # Fallback to local SQL parser if MySQL is not reachable
        pass
    return None

def load_sales_from_sql_seed(seed_path=None):
    """
    Parses seed.sql and populates an in-memory SQLite database to extract
    the identical relational dataset when running offline.
    """
    if seed_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        seed_path = os.path.join(base_dir, "database", "seed.sql")

    if not os.path.exists(seed_path):
        raise FileNotFoundError(f"Seed file not found at {seed_path}")

    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Create schema tables
    cursor.execute("CREATE TABLE IF NOT EXISTS stores (store_id INTEGER PRIMARY KEY, name TEXT, owner_name TEXT, currency TEXT, currency_symbol TEXT, created_at TIMESTAMP);")
    cursor.execute("CREATE TABLE IF NOT EXISTS suppliers (supplier_id INTEGER PRIMARY KEY, store_id INTEGER, name TEXT, contact_name TEXT, email TEXT, phone TEXT, lead_time_days INTEGER, created_at TIMESTAMP);")
    cursor.execute("CREATE TABLE IF NOT EXISTS products (product_id INTEGER PRIMARY KEY, store_id INTEGER, supplier_id INTEGER, sku TEXT, name TEXT, category TEXT, cost_price REAL, selling_price REAL, created_at TIMESTAMP);")
    cursor.execute("CREATE TABLE IF NOT EXISTS inventory (inventory_id INTEGER PRIMARY KEY, product_id INTEGER, current_stock INTEGER, min_stock_level INTEGER, max_stock_level INTEGER, safety_stock INTEGER, lead_time_days INTEGER, last_updated TIMESTAMP);")
    cursor.execute("CREATE TABLE IF NOT EXISTS sales (sale_id INTEGER PRIMARY KEY, store_id INTEGER, receipt_number TEXT, total_amount REAL, payment_method TEXT, sale_date TEXT);")
    cursor.execute("CREATE TABLE IF NOT EXISTS sale_items (sale_item_id INTEGER PRIMARY KEY, sale_id INTEGER, product_id INTEGER, quantity INTEGER, unit_price REAL, unit_cost REAL);")

    with open(seed_path, "r", encoding="utf-8") as f:
        seed_sql = f.read()

    # Clean MySQL syntax
    seed_sql = re.sub(r'SET FOREIGN_KEY_CHECKS\s*=\s*[01];', '', seed_sql, flags=re.IGNORECASE)
    seed_sql = re.sub(r'TRUNCATE TABLE\s+[a-zA-Z0-9_]+;', '', seed_sql, flags=re.IGNORECASE)
    seed_sql = re.sub(r'USE [^;]+;', '', seed_sql, flags=re.IGNORECASE)

    current = []
    for line in seed_sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") or not stripped:
            continue
        if "--" in line:
            line = re.sub(r'--.*$', '', line)
        current.append(line)
        if ";" in line:
            full_stmt = "\n".join(current).strip()
            if full_stmt:
                try:
                    cursor.execute(full_stmt)
                except Exception as e:
                    pass
            current = []

    conn.commit()

    query = """
        SELECT 
            s.sale_id,
            s.sale_date,
            s.receipt_number,
            s.payment_method,
            si.sale_item_id,
            si.product_id,
            p.sku,
            p.name AS product_name,
            p.category,
            si.quantity,
            si.unit_price,
            si.unit_cost
        FROM sales s
        JOIN sale_items si ON s.sale_id = si.sale_id
        JOIN products p ON si.product_id = p.product_id
        ORDER BY s.sale_date ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def validate_raw_sales_data(df):
    """
    Validates the raw sales dataset:
    - Verifies product_id, sale_date, and quantity are not null.
    - Flags and drops negative or zero quantities.
    - Ensures date strings can be parsed to timestamps.
    - Generates a data quality summary report.
    """
    quality_report = {
        "total_raw_records": len(df),
        "missing_product_ids": int(df["product_id"].isna().sum()),
        "missing_dates": int(df["sale_date"].isna().sum()),
        "invalid_quantities": int((df["quantity"] <= 0).sum()) if "quantity" in df else 0,
        "duplicate_item_records": int(df.duplicated(subset=["sale_id", "product_id"]).sum()) if "sale_id" in df else 0,
        "dropped_records": 0,
        "status": "PASS"
    }

    # Filter invalid records safely
    initial_count = len(df)
    clean_df = df.dropna(subset=["product_id", "sale_date", "quantity"]).copy()
    clean_df = clean_df[clean_df["quantity"] > 0]
    
    # Parse dates
    clean_df["sale_date"] = pd.to_datetime(clean_df["sale_date"])
    clean_df["quantity"] = clean_df["quantity"].astype(int)
    clean_df["product_id"] = clean_df["product_id"].astype(int)

    quality_report["dropped_records"] = initial_count - len(clean_df)
    quality_report["valid_records_count"] = len(clean_df)
    quality_report["unique_products_count"] = int(clean_df["product_id"].nunique())
    quality_report["date_range_start"] = clean_df["sale_date"].min().strftime("%Y-%m-%d")
    quality_report["date_range_end"] = clean_df["sale_date"].max().strftime("%Y-%m-%d")

    return clean_df, quality_report

def load_sales_from_sqlite(db_path=None):
    """Attempts to query the local SQLite database directly if present."""
    if db_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "database", "smart_retail.db")

    if not os.path.exists(db_path):
        return None

    try:
        conn = sqlite3.connect(db_path)
        query = """
            SELECT 
                s.sale_id,
                s.sale_date,
                s.receipt_number,
                s.payment_method,
                si.sale_item_id,
                si.product_id,
                p.sku,
                p.name AS product_name,
                p.category,
                si.quantity,
                si.unit_price,
                si.unit_cost
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            JOIN products p ON si.product_id = p.product_id
            ORDER BY s.sale_date ASC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        if len(df) > 0:
            return df
    except Exception:
        pass
    return None

def get_raw_sales_data():
    """Unified entry point to fetch and validate historical sales data."""
    df = load_sales_from_mysql()
    if df is None or len(df) == 0:
        df = load_sales_from_sqlite()
    if df is None or len(df) == 0:
        df = load_sales_from_sql_seed()
    
    clean_df, quality_report = validate_raw_sales_data(df)
    return clean_df, quality_report

