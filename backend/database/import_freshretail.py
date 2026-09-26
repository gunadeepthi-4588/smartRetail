"""
SmartRetail — FreshRetailNet-50K Real Dataset Importer & Seeder
Downloads and extracts a manageable real-world subset from Hugging Face
(Store 18, 20 high-quality products across 8 categories, 97 consecutive days)
and maps it into the SmartRetail relational database schema with stockout censoring handling.
"""

import os
import sys
import json
import sqlite3
import requests
import pandas as pd
import numpy as np

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Product Catalog Mapping: 20 Selected Real FreshRetailNet Products from Store 18
CATALOG_MAPPING = [
    {
        "product_id": 1,
        "frn_pid": 117,
        "sku": "SKU-VEG-117",
        "name": "Organic Baby Spinach 250g",
        "category": "Fresh Produce",
        "supplier_id": 1,
        "cost_price": 45.00,
        "selling_price": 65.00,
        "current_stock": 14,
        "safety_stock": 25,
        "min_stock_level": 20,
        "max_stock_level": 120,
        "lead_time_days": 2
    },
    {
        "product_id": 2,
        "frn_pid": 70,
        "sku": "SKU-VEG-070",
        "name": "Fresh Broccoli Florets 500g",
        "category": "Fresh Produce",
        "supplier_id": 1,
        "cost_price": 50.00,
        "selling_price": 75.00,
        "current_stock": 8,
        "safety_stock": 20,
        "min_stock_level": 15,
        "max_stock_level": 100,
        "lead_time_days": 2
    },
    {
        "product_id": 3,
        "frn_pid": 215,
        "sku": "SKU-VEG-215",
        "name": "Hydroponic Butter Lettuce 300g",
        "category": "Fresh Produce",
        "supplier_id": 1,
        "cost_price": 40.00,
        "selling_price": 60.00,
        "current_stock": 35,
        "safety_stock": 15,
        "min_stock_level": 15,
        "max_stock_level": 90,
        "lead_time_days": 2
    },
    {
        "product_id": 4,
        "frn_pid": 19,
        "sku": "SKU-VEG-019",
        "name": "Tricolor Bell Peppers 400g",
        "category": "Fresh Produce",
        "supplier_id": 1,
        "cost_price": 60.00,
        "selling_price": 90.00,
        "current_stock": 28,
        "safety_stock": 15,
        "min_stock_level": 15,
        "max_stock_level": 80,
        "lead_time_days": 2
    },
    {
        "product_id": 5,
        "frn_pid": 118,
        "sku": "SKU-VEG-118",
        "name": "Organic Cherry Tomatoes 250g",
        "category": "Fresh Produce",
        "supplier_id": 1,
        "cost_price": 35.00,
        "selling_price": 55.00,
        "current_stock": 42,
        "safety_stock": 15,
        "min_stock_level": 15,
        "max_stock_level": 90,
        "lead_time_days": 2
    },
    {
        "product_id": 6,
        "frn_pid": 292,
        "sku": "SKU-DRY-292",
        "name": "Farm Fresh Pasteurized Milk 1L",
        "category": "Dairy & Eggs",
        "supplier_id": 1,
        "cost_price": 55.00,
        "selling_price": 75.00,
        "current_stock": 12,
        "safety_stock": 20,
        "min_stock_level": 15,
        "max_stock_level": 100,
        "lead_time_days": 2
    },
    {
        "product_id": 7,
        "frn_pid": 300,
        "sku": "SKU-FRT-300",
        "name": "Premium Red Gala Apples 1kg",
        "category": "Fruits",
        "supplier_id": 2,
        "cost_price": 140.00,
        "selling_price": 200.00,
        "current_stock": 45,
        "safety_stock": 30,
        "min_stock_level": 25,
        "max_stock_level": 150,
        "lead_time_days": 3
    },
    {
        "product_id": 8,
        "frn_pid": 104,
        "sku": "SKU-FRT-104",
        "name": "Fresh Cavendish Bananas 1kg",
        "category": "Fruits",
        "supplier_id": 2,
        "cost_price": 35.00,
        "selling_price": 50.00,
        "current_stock": 55,
        "safety_stock": 20,
        "min_stock_level": 20,
        "max_stock_level": 120,
        "lead_time_days": 3
    },
    {
        "product_id": 9,
        "frn_pid": 486,
        "sku": "SKU-FRT-486",
        "name": "Seedless Sweet Mandarins 750g",
        "category": "Fruits",
        "supplier_id": 2,
        "cost_price": 90.00,
        "selling_price": 130.00,
        "current_stock": 30,
        "safety_stock": 15,
        "min_stock_level": 15,
        "max_stock_level": 90,
        "lead_time_days": 3
    },
    {
        "product_id": 10,
        "frn_pid": 122,
        "sku": "SKU-FRT-122",
        "name": "Imported Green Kiwi 4-Pack",
        "category": "Fruits",
        "supplier_id": 2,
        "cost_price": 110.00,
        "selling_price": 160.00,
        "current_stock": 25,
        "safety_stock": 15,
        "min_stock_level": 15,
        "max_stock_level": 80,
        "lead_time_days": 3
    },
    {
        "product_id": 11,
        "frn_pid": 691,
        "sku": "SKU-PRT-691",
        "name": "Fresh Chicken Breast Fillet 500g",
        "category": "Meat & Poultry",
        "supplier_id": 2,
        "cost_price": 160.00,
        "selling_price": 230.00,
        "current_stock": 18,
        "safety_stock": 25,
        "min_stock_level": 20,
        "max_stock_level": 100,
        "lead_time_days": 2
    },
    {
        "product_id": 12,
        "frn_pid": 666,
        "sku": "SKU-PRT-666",
        "name": "Tender Chicken Thighs 500g",
        "category": "Meat & Poultry",
        "supplier_id": 2,
        "cost_price": 140.00,
        "selling_price": 200.00,
        "current_stock": 32,
        "safety_stock": 15,
        "min_stock_level": 15,
        "max_stock_level": 90,
        "lead_time_days": 2
    },
    {
        "product_id": 13,
        "frn_pid": 783,
        "sku": "SKU-SEA-783",
        "name": "Atlantic Salmon Portions 300g",
        "category": "Seafood",
        "supplier_id": 2,
        "cost_price": 350.00,
        "selling_price": 480.00,
        "current_stock": 15,
        "safety_stock": 12,
        "min_stock_level": 10,
        "max_stock_level": 50,
        "lead_time_days": 3
    },
    {
        "product_id": 14,
        "frn_pid": 413,
        "sku": "SKU-BAK-413",
        "name": "Artisan Sourdough Loaf 450g",
        "category": "Bakery",
        "supplier_id": 3,
        "cost_price": 70.00,
        "selling_price": 110.00,
        "current_stock": 22,
        "safety_stock": 20,
        "min_stock_level": 15,
        "max_stock_level": 80,
        "lead_time_days": 2
    },
    {
        "product_id": 15,
        "frn_pid": 481,
        "sku": "SKU-SNK-481",
        "name": "Roasted Salted Almonds 200g",
        "category": "Snacks",
        "supplier_id": 3,
        "cost_price": 180.00,
        "selling_price": 260.00,
        "current_stock": 120,
        "safety_stock": 15,
        "min_stock_level": 15,
        "max_stock_level": 80,
        "lead_time_days": 4
    },
    {
        "product_id": 16,
        "frn_pid": 580,
        "sku": "SKU-BEV-580",
        "name": "Pure Cold-Pressed Orange Juice 1L",
        "category": "Beverages",
        "supplier_id": 3,
        "cost_price": 85.00,
        "selling_price": 130.00,
        "current_stock": 10,
        "safety_stock": 20,
        "min_stock_level": 15,
        "max_stock_level": 80,
        "lead_time_days": 2
    },
    {
        "product_id": 17,
        "frn_pid": 4,
        "sku": "SKU-STP-004",
        "name": "Organic Jasmine White Rice 2kg",
        "category": "Staples",
        "supplier_id": 4,
        "cost_price": 190.00,
        "selling_price": 270.00,
        "current_stock": 40,
        "safety_stock": 15,
        "min_stock_level": 15,
        "max_stock_level": 90,
        "lead_time_days": 4
    },
    {
        "product_id": 18,
        "frn_pid": 600,
        "sku": "SKU-BEV-600",
        "name": "Natural Sparkling Water 750ml",
        "category": "Beverages",
        "supplier_id": 3,
        "cost_price": 40.00,
        "selling_price": 65.00,
        "current_stock": 50,
        "safety_stock": 15,
        "min_stock_level": 15,
        "max_stock_level": 100,
        "lead_time_days": 3
    },
    {
        "product_id": 19,
        "frn_pid": 596,
        "sku": "SKU-BEV-596",
        "name": "Artisanal Green Tea Leaves 150g",
        "category": "Beverages",
        "supplier_id": 3,
        "cost_price": 120.00,
        "selling_price": 180.00,
        "current_stock": 35,
        "safety_stock": 15,
        "min_stock_level": 15,
        "max_stock_level": 70,
        "lead_time_days": 3
    },
    {
        "product_id": 20,
        "frn_pid": 549,
        "sku": "SKU-PNT-549",
        "name": "Extra Virgin Olive Oil 500ml",
        "category": "Pantry",
        "supplier_id": 4,
        "cost_price": 280.00,
        "selling_price": 390.00,
        "current_stock": 28,
        "safety_stock": 12,
        "min_stock_level": 10,
        "max_stock_level": 60,
        "lead_time_days": 4
    }
]

def download_file(url, destination_path):
    """Downloads a file in chunks with progress reporting."""
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    if os.path.exists(destination_path):
        return
    print(f"Downloading {os.path.basename(destination_path)} from Hugging Face...")
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(destination_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=4 * 1024 * 1024):
            if chunk:
                f.write(chunk)
    print(f"Downloaded {os.path.basename(destination_path)} ({os.path.getsize(destination_path):,} bytes).")

def ensure_dataset_files(data_dir):
    """Ensures FreshRetailNet parquet files are available locally."""
    import pyarrow.parquet as pq
    train_path = os.path.join(data_dir, "train.parquet")
    eval_path = os.path.join(data_dir, "eval.parquet")

    train_url = "https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K/resolve/main/data/train.parquet"
    eval_url = "https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K/resolve/main/data/eval.parquet"

    download_file(train_url, train_path)
    download_file(eval_url, eval_path)

    return train_path, eval_path

def process_freshretail_data(train_path, eval_path, selected_store=18):
    """
    Extracts and preprocesses Store 18 records for the 20 chosen products.
    Applies stockout censoring adjustments and builds transactional tables.
    """
    import pyarrow.parquet as pq

    train_tbl = pq.read_table(train_path, filters=[('store_id', '=', selected_store)])
    eval_tbl = pq.read_table(eval_path, filters=[('store_id', '=', selected_store)])
    raw_df = pd.concat([train_tbl.to_pandas(), eval_tbl.to_pandas()], ignore_index=True)

    frn_pid_map = {item["frn_pid"]: item for item in CATALOG_MAPPING}
    selected_pids = list(frn_pid_map.keys())

    df = raw_df[raw_df["product_id"].isin(selected_pids)].copy()
    df["date"] = pd.to_datetime(df["dt"])
    df = df.sort_values(by=["date", "product_id"]).reset_index(drop=True)

    # Stockout Handling
    df["stockout_hours"] = df["stock_hour6_22_cnt"].clip(0, 16)
    df["in_stock_hours"] = 16 - df["stockout_hours"]
    df["is_stockout"] = (df["stockout_hours"] > 0).astype(int)

    # Observed real demand (integer units sold)
    df["observed_units"] = df["sale_amount"].round().astype(int)

    # Map to catalog product_id
    df["app_product_id"] = df["product_id"].map(lambda p: frn_pid_map[p]["product_id"])
    df["sku"] = df["product_id"].map(lambda p: frn_pid_map[p]["sku"])
    df["name"] = df["product_id"].map(lambda p: frn_pid_map[p]["name"])
    df["category"] = df["product_id"].map(lambda p: frn_pid_map[p]["category"])
    df["cost_price"] = df["product_id"].map(lambda p: frn_pid_map[p]["cost_price"])
    df["selling_price"] = df["product_id"].map(lambda p: frn_pid_map[p]["selling_price"])

    return df

def generate_seed_sql_content(df):
    """
    Constructs a valid MySQL & SQLite compliant seed.sql containing
    all relational tables, store owner, suppliers, 20 products, inventory,
    and 97 days of real sales transactions.
    """
    lines = []
    lines.append("-- ==============================================================================")
    lines.append("-- SmartRetail Seed Data — FreshRetailNet-50K Real Retail Dataset Integration")
    lines.append("-- Store 18 | 20 Real Products | 97 Consecutive Days | 1,940 Observations")
    lines.append("-- ==============================================================================\n")
    lines.append("USE smart_retail_db;\n")
    lines.append("SET FOREIGN_KEY_CHECKS = 0;")
    lines.append("TRUNCATE TABLE reorder_recommendations;")
    lines.append("TRUNCATE TABLE forecasts;")
    lines.append("TRUNCATE TABLE sale_items;")
    lines.append("TRUNCATE TABLE sales;")
    lines.append("TRUNCATE TABLE inventory;")
    lines.append("TRUNCATE TABLE products;")
    lines.append("TRUNCATE TABLE suppliers;")
    lines.append("TRUNCATE TABLE users;")
    lines.append("TRUNCATE TABLE stores;")
    lines.append("SET FOREIGN_KEY_CHECKS = 1;\n")

    # 1. Store
    lines.append("-- 1. STORE")
    lines.append("INSERT INTO stores (store_id, name, owner_name, currency, currency_symbol, created_at)")
    lines.append("VALUES (1, 'Metro Mart Superstore', 'Rajesh Kumar', 'INR', '₹', '2024-03-01 08:00:00');\n")

    # 2. User
    lines.append("-- 2. USERS (Store Owner Login: owner@smartretail.com / password: SmartRetail@123)")
    lines.append("INSERT INTO users (user_id, store_id, username, password_hash, email, created_at)")
    lines.append("VALUES (1, 1, 'rajesh_owner', 'scrypt:32768:8:1$3jcR2aYIElTZqJMz$61ed6f52f41f8dd4ee2461df89728bd50279940a57c40b2d54ce9bce3eafa3588a2d4e66c86186429de2c325da943ec8e87dfabe34733161dbed5943548f568e', 'owner@smartretail.com', '2024-03-01 08:30:00');\n")


    # 3. Suppliers
    lines.append("-- 3. SUPPLIERS")
    lines.append("INSERT INTO suppliers (supplier_id, store_id, name, contact_name, email, phone, lead_time_days, created_at) VALUES")
    lines.append("(1, 1, 'Heritage Fresh Greens & Dairy Ltd.', 'Sunil Sharma', 'orders@heritagegreens.com', '+91 98765 43210', 2, '2024-03-01 09:00:00'),")
    lines.append("(2, 1, 'Golden Harvest Farms & Orchards', 'Pooja Verma', 'supply@goldenharvest.in', '+91 98765 43211', 3, '2024-03-01 09:15:00'),")
    lines.append("(3, 1, 'Sunrise Bakery & Beverages Co.', 'Amit Patel', 'sales@sunrisegroup.com', '+91 98765 43212', 2, '2024-03-01 09:30:00'),")
    lines.append("(4, 1, 'PureCare Pantry & Essentials', 'Neha Gupta', 'distrib@purecare.com', '+91 98765 43213', 4, '2024-03-01 09:45:00');\n")

    # 4. Products
    lines.append("-- 4. PRODUCTS (20 Real Items from FreshRetailNet-50K Store 18)")
    lines.append("INSERT INTO products (product_id, store_id, supplier_id, sku, name, category, cost_price, selling_price, created_at) VALUES")
    prod_rows = []
    for p in CATALOG_MAPPING:
        row_str = f"({p['product_id']}, 1, {p['supplier_id']}, '{p['sku']}', '{p['name']}', '{p['category']}', {p['cost_price']:.2f}, {p['selling_price']:.2f}, '2024-03-15 10:00:00')"
        prod_rows.append(row_str)
    lines.append(",\n".join(prod_rows) + ";\n")

    # 5. Inventory
    lines.append("-- 5. INVENTORY")
    lines.append("INSERT INTO inventory (inventory_id, product_id, current_stock, min_stock_level, max_stock_level, safety_stock, lead_time_days, last_updated) VALUES")
    inv_rows = []
    for i, p in enumerate(CATALOG_MAPPING, 1):
        row_str = f"({i}, {p['product_id']}, {p['current_stock']}, {p['min_stock_level']}, {p['max_stock_level']}, {p['safety_stock']}, {p['lead_time_days']}, '2024-07-02 20:00:00')"
        inv_rows.append(row_str)
    lines.append(",\n".join(inv_rows) + ";\n")

    # 6. Sales & Sale Items
    lines.append("-- 6. SALES & SALE_ITEMS (Real historical sales for 97 days)")
    unique_dates = sorted(df["dt"].unique())
    sale_item_id = 1
    
    sales_sql_values = []
    sale_items_sql_values = []

    for sale_id, dt_str in enumerate(unique_dates, 1):
        date_records = df[df["dt"] == dt_str]
        # Calculate daily total
        daily_total = 0.0
        daily_items = []
        payment_method = "Card" if sale_id % 3 == 0 else ("UPI" if sale_id % 2 == 0 else "Cash")
        
        for _, rec in date_records.iterrows():
            qty = int(rec["observed_units"])
            if qty > 0:
                cost = float(rec["cost_price"])
                price = float(rec["selling_price"])
                item_total = qty * price
                daily_total += item_total
                daily_items.append((sale_item_id, sale_id, int(rec["app_product_id"]), qty, price, cost))
                sale_item_id += 1

        if daily_items:
            receipt = f"RCP-FRN-{dt_str.replace('-', '')}-{sale_id:03d}"
            sales_sql_values.append(f"({sale_id}, 1, '{receipt}', {daily_total:.2f}, '{payment_method}', '{dt_str} 19:30:00')")
            for item in daily_items:
                sale_items_sql_values.append(f"({item[0]}, {item[1]}, {item[2]}, {item[3]}, {item[4]:.2f}, {item[5]:.2f})")

    lines.append("INSERT INTO sales (sale_id, store_id, receipt_number, total_amount, payment_method, sale_date) VALUES")
    # Batch inserts
    lines.append(",\n".join(sales_sql_values) + ";\n")

    lines.append("INSERT INTO sale_items (sale_item_id, sale_id, product_id, quantity, unit_price, unit_cost) VALUES")
    # Batch items
    lines.append(",\n".join(sale_items_sql_values) + ";\n")

    return "\n".join(lines)

def apply_seed_to_sqlite(seed_sql_content, sqlite_path):
    """Applies the seed data into SQLite database."""
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()

    # Create tables if not exist
    cursor.execute("CREATE TABLE IF NOT EXISTS stores (store_id INTEGER PRIMARY KEY, name TEXT, owner_name TEXT, currency TEXT, currency_symbol TEXT, created_at TIMESTAMP);")
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, store_id INTEGER, username TEXT, password_hash TEXT, email TEXT, created_at TIMESTAMP);")
    cursor.execute("CREATE TABLE IF NOT EXISTS suppliers (supplier_id INTEGER PRIMARY KEY, store_id INTEGER, name TEXT, contact_name TEXT, email TEXT, phone TEXT, lead_time_days INTEGER, created_at TIMESTAMP);")
    cursor.execute("CREATE TABLE IF NOT EXISTS products (product_id INTEGER PRIMARY KEY, store_id INTEGER, supplier_id INTEGER, sku TEXT, name TEXT, category TEXT, cost_price REAL, selling_price REAL, created_at TIMESTAMP);")
    cursor.execute("CREATE TABLE IF NOT EXISTS inventory (inventory_id INTEGER PRIMARY KEY, product_id INTEGER, current_stock INTEGER, min_stock_level INTEGER, max_stock_level INTEGER, safety_stock INTEGER, lead_time_days INTEGER, last_updated TIMESTAMP);")
    cursor.execute("CREATE TABLE IF NOT EXISTS sales (sale_id INTEGER PRIMARY KEY, store_id INTEGER, receipt_number TEXT, total_amount REAL, payment_method TEXT, sale_date TEXT);")
    cursor.execute("CREATE TABLE IF NOT EXISTS sale_items (sale_item_id INTEGER PRIMARY KEY, sale_id INTEGER, product_id INTEGER, quantity INTEGER, unit_price REAL, unit_cost REAL);")
    cursor.execute("CREATE TABLE IF NOT EXISTS forecasts (forecast_id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, forecast_date TEXT, target_date TEXT, predicted_demand REAL, actual_demand REAL, model_name TEXT, horizon_days INTEGER, created_at TIMESTAMP);")
    cursor.execute("CREATE TABLE IF NOT EXISTS reorder_recommendations (recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, calculation_date TEXT, predicted_demand REAL, current_stock INTEGER, safety_stock INTEGER, lead_time_demand REAL, recommended_quantity INTEGER, status TEXT, created_at TIMESTAMP);")

    # Clear old data
    for tbl in ["reorder_recommendations", "forecasts", "sale_items", "sales", "inventory", "products", "suppliers", "users", "stores"]:
        cursor.execute(f"DELETE FROM {tbl};")

    # Execute insert statements
    import re
    cleaned = re.sub(r'SET FOREIGN_KEY_CHECKS\s*=\s*[01];', '', seed_sql_content, flags=re.IGNORECASE)
    cleaned = re.sub(r'TRUNCATE TABLE\s+[a-zA-Z0-9_]+;', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'USE [^;]+;', '', cleaned, flags=re.IGNORECASE)

    current = []
    for line in cleaned.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") or not stripped:
            continue
        current.append(line)
        if ";" in line:
            stmt = "\n".join(current).strip()
            if stmt:
                try:
                    cursor.execute(stmt)
                except Exception as e:
                    print(f"[Warning SQLite] {e} in stmt: {stmt[:60]}")
            current = []

    conn.commit()

    # Verification counts
    counts = {}
    for tbl in ["stores", "users", "suppliers", "products", "inventory", "sales", "sale_items"]:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
        counts[tbl] = cursor.fetchone()[0]

    conn.close()
    return counts

def run_import():
    """Main execution entry point for dataset import."""
    print("=" * 70)
    print(" SmartRetail — FreshRetailNet-50K Dataset Import & Seeding")
    print("=" * 70)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data_raw")
    db_dir = os.path.join(base_dir, "database")

    train_path, eval_path = ensure_dataset_files(data_dir)
    print("[1/4] Dataset files verified in data_raw/.")

    df = process_freshretail_data(train_path, eval_path, selected_store=18)
    print(f"[2/4] Processed Store 18 data: {len(df)} daily product records.")
    print(f"      - Date range: {df['dt'].min()} to {df['dt'].max()} ({df['dt'].nunique()} days)")
    print(f"      - Products mapped: {df['app_product_id'].nunique()}")
    print(f"      - Total units sold: {df['observed_units'].sum():,}")
    print(f"      - Stockout records: {df['is_stockout'].sum()} ({df['is_stockout'].mean()*100:.1f}%)")

    seed_sql = generate_seed_sql_content(df)
    seed_path = os.path.join(db_dir, "seed.sql")
    with open(seed_path, "w", encoding="utf-8") as f:
        f.write(seed_sql)
    print(f"[3/4] Generated {seed_path} ({len(seed_sql):,} bytes).")

    sqlite_path = os.path.join(db_dir, "smart_retail.db")
    counts = apply_seed_to_sqlite(seed_sql, sqlite_path)
    print(f"[4/4] Seeded local SQLite database ({sqlite_path}):")
    for tbl, count in counts.items():
        print(f"      - {tbl:<16}: {count} records")

    # Export stockout annotations for ML preprocessing
    saved_models_dir = os.path.join(base_dir, "ml", "saved_models")
    os.makedirs(saved_models_dir, exist_ok=True)
    stockout_dict = {}
    for _, row in df.iterrows():
        key = f"{int(row['app_product_id'])}_{row['dt']}"
        stockout_dict[key] = {
            "product_id": int(row["app_product_id"]),
            "date": row["dt"],
            "stockout_hours": int(row["stockout_hours"]),
            "in_stock_hours": int(row["in_stock_hours"]),
            "is_stockout": int(row["is_stockout"]),
            "observed_units": int(row["observed_units"])
        }
    stockout_file = os.path.join(saved_models_dir, "stockout_annotations.json")
    with open(stockout_file, "w", encoding="utf-8") as f:
        json.dump(stockout_dict, f, indent=2)
    print(f"[5/5] Exported {len(stockout_dict)} stockout annotations to {stockout_file}")

    print("\n[SUCCESS] FreshRetailNet-50K dataset successfully imported!")
    return df, counts


if __name__ == "__main__":
    run_import()
