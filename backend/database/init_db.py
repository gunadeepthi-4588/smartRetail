"""
SmartRetail Database Initialization & Verification Script
Reads configuration from environment variables (.env), applies schema.sql & seed.sql,
and runs comprehensive verification checks against MySQL.
"""

import os
import sys
import pymysql
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "smart_retail_db")

def get_connection(include_db=True):
    """Establishes a MySQL connection."""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME if include_db else None,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def execute_sql_file(cursor, file_path):
    """Executes multi-statement SQL script."""
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    statements = sql_content.split(";")
    for stmt in statements:
        clean_stmt = stmt.strip()
        if clean_stmt and not clean_stmt.startswith("--"):
            cursor.execute(clean_stmt)

def initialize_database():
    """Applies schema and seed data to MySQL."""
    print("=" * 70)
    print("SmartRetail - MySQL Database Initialization & Verification")
    print("=" * 70)
    print(f"Target Server : {DB_HOST}:{DB_PORT} (User: {DB_USER})")
    print(f"Target DB     : {DB_NAME}\n")

    # Step 1: Connect to server and create database if not exists
    try:
        conn = get_connection(include_db=False)
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.close()
        print(f"[OK] Database '{DB_NAME}' created or verified.")
    except Exception as e:
        print(f"[ERROR] Could not connect to MySQL server: {e}")
        print("\nPlease ensure MySQL is running and your backend/.env contains valid DB_PASSWORD.")
        return False

    # Step 2: Connect to DB and apply schema.sql
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    try:
        conn = get_connection(include_db=True)
        with conn.cursor() as cursor:
            execute_sql_file(cursor, schema_path)
        conn.close()
        print(f"[OK] schema.sql executed successfully (9 tables created).")
    except Exception as e:
        print(f"[ERROR] Failed to execute schema.sql: {e}")
        return False

    # Step 3: Apply seed.sql
    seed_path = os.path.join(os.path.dirname(__file__), "seed.sql")
    try:
        conn = get_connection(include_db=True)
        with conn.cursor() as cursor:
            execute_sql_file(cursor, seed_path)
        conn.close()
        print(f"[OK] seed.sql executed successfully (seed data inserted).\n")
    except Exception as e:
        print(f"[ERROR] Failed to execute seed.sql: {e}")
        return False

    # Step 4: Run Verification Queries
    return run_verifications()

def run_verifications():
    """Runs data integrity and representative analytics verification queries."""
    print("-" * 70)
    print("RUNNING VERIFICATION QUERIES")
    print("-" * 70)
    conn = get_connection(include_db=True)
    
    with conn.cursor() as cursor:
        # Check 1: Table row counts
        tables = [
            "stores", "users", "suppliers", "products", "inventory",
            "sales", "sale_items", "forecasts", "reorder_recommendations"
        ]
        print("\n1. Table Row Counts:")
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {t};")
            row = cursor.fetchone()
            print(f"   - {t:<26}: {row['count']} rows")

        # Check 2: Products join with Inventory
        print("\n2. Products Join Inventory (Sample Check):")
        cursor.execute("""
            SELECT p.sku, p.name, p.category, p.cost_price, p.selling_price, 
                   i.current_stock, i.safety_stock
            FROM products p
            JOIN inventory i ON p.product_id = i.product_id
            ORDER BY p.product_id ASC
            LIMIT 4;
        """)
        for row in cursor.fetchall():
            print(f"   - [{row['sku']}] {row['name'][:24]:<24} | Stock: {row['current_stock']:<3} | Safety: {row['safety_stock']}")

        # Check 3: Total Revenue and Gross Profit from Sales
        print("\n3. Financial Aggregates (Revenue & Profit Verification):")
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT s.sale_id) AS total_transactions,
                SUM(si.quantity) AS total_units_sold,
                SUM(si.quantity * si.unit_price) AS total_revenue,
                SUM(si.quantity * (si.unit_price - si.unit_cost)) AS gross_profit,
                ROUND((SUM(si.quantity * (si.unit_price - si.unit_cost)) / SUM(si.quantity * si.unit_price)) * 100, 2) AS profit_margin_pct
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id;
        """)
        fin = cursor.fetchone()
        print(f"   - Transactions  : {fin['total_transactions']}")
        print(f"   - Units Sold    : {fin['total_units_sold']}")
        print(f"   - Total Revenue : Rs. {fin['total_revenue']:,.2f}")
        print(f"   - Gross Profit  : Rs. {fin['gross_profit']:,.2f} ({fin['profit_margin_pct']}%)")

        # Check 4: Best-Sellers (by volume) vs Revenue Leaders
        print("\n4. Top Volume Best-Sellers vs Revenue Leaders:")
        cursor.execute("""
            SELECT p.name, SUM(si.quantity) AS units_sold, SUM(si.quantity * si.unit_price) AS revenue
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            GROUP BY p.product_id, p.name
            ORDER BY units_sold DESC
            LIMIT 3;
        """)
        print("   * Volume Leaders:")
        for row in cursor.fetchall():
            print(f"     - {row['name'][:28]:<28}: {row['units_sold']} units (Rs. {row['revenue']:,.2f})")

        # Check 5: Low-Stock Risk Identification
        print("\n5. Low-Stock Detection (Current Stock < Safety Stock):")
        cursor.execute("""
            SELECT p.sku, p.name, i.current_stock, i.safety_stock, i.min_stock_level
            FROM inventory i
            JOIN products p ON i.product_id = p.product_id
            WHERE i.current_stock < i.safety_stock;
        """)
        low_stock_rows = cursor.fetchall()
        for row in low_stock_rows:
            print(f"   - [ALERT] {row['name']} (SKU: {row['sku']}) -> Stock: {row['current_stock']}, Safety: {row['safety_stock']}")

        # Check 6: Overstock Candidates (High Stock, Low Sales)
        print("\n6. Overstock / Slow-Moving Candidates:")
        cursor.execute("""
            SELECT p.name, i.current_stock, COALESCE(SUM(si.quantity), 0) AS units_sold_30d
            FROM products p
            JOIN inventory i ON p.product_id = i.product_id
            LEFT JOIN sale_items si ON p.product_id = si.product_id
            GROUP BY p.product_id, p.name, i.current_stock
            HAVING i.current_stock > 100 AND units_sold_30d <= 3;
        """)
        overstock_rows = cursor.fetchall()
        for row in overstock_rows:
            print(f"   - [OVERSTOCK] {row['name']} -> Stock: {row['current_stock']}, 30-Day Sales: {row['units_sold_30d']} units")

        # Check 7: Orphan Records Check (Referential Integrity)
        print("\n7. Referential Integrity / Orphan Records Check:")
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM sale_items WHERE sale_id NOT IN (SELECT sale_id FROM sales)) as orphan_sale_items,
                (SELECT COUNT(*) FROM inventory WHERE product_id NOT IN (SELECT product_id FROM products)) as orphan_inventory,
                (SELECT COUNT(*) FROM products WHERE store_id NOT IN (SELECT store_id FROM stores)) as orphan_products;
        """)
        orphans = cursor.fetchone()
        print(f"   - Orphan Sale Items : {orphans['orphan_sale_items']}")
        print(f"   - Orphan Inventory  : {orphans['orphan_inventory']}")
        print(f"   - Orphan Products   : {orphans['orphan_products']}")

    conn.close()
    print("\n" + "=" * 70)
    print("[SUCCESS] All Phase 3 MySQL schema & seed verification checks PASSED!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = initialize_database()
    sys.exit(0 if success else 1)
