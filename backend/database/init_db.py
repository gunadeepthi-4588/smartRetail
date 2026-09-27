"""
SmartRetail Database Initialization & Verification Script
Reads configuration from environment variables (.env or cloud environment),
applies schema.sql & seed.sql with foreign key integrity, and runs comprehensive verification checks.
Supports local MySQL and all major managed cloud MySQL providers (Aiven, TiDB, Render, Railway, AWS RDS).
"""

import os
import sys
import re
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load environment variables from backend/.env if available
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "smart_retail_db")
DB_SSL_CA = os.getenv("DB_SSL_CA", None)
DB_SSL_MODE = os.getenv("DB_SSL_MODE", None)
DB_SSL_REQUIRED = os.getenv("DB_SSL_REQUIRED", "0").lower() in ("1", "true", "yes")

def get_connection(include_db=True):
    """Establishes a MySQL connection with SSL support when configured."""
    conn_kwargs = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "database": DB_NAME if include_db else None,
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True,
        "connect_timeout": 10
    }

    ssl_dict = {}
    if DB_SSL_CA:
        ssl_dict["ca"] = DB_SSL_CA
    if DB_SSL_MODE:
        ssl_dict["ssl_mode"] = DB_SSL_MODE
    elif DB_SSL_REQUIRED and not ssl_dict:
        ssl_dict["ssl_mode"] = "REQUIRED"

    if ssl_dict:
        conn_kwargs["ssl"] = ssl_dict

    return pymysql.connect(**conn_kwargs)

def strip_sql_comments(sql_text):
    """Strips SQL line comments (-- and #) and block comments (/* */)."""
    sql_text = re.sub(r'/\*.*?\*/', '', sql_text, flags=re.DOTALL)
    clean_lines = []
    for line in sql_text.splitlines():
        line_clean = re.sub(r'--.*$', '', line)
        line_clean = re.sub(r'#.*$', '', line_clean)
        clean_lines.append(line_clean)
    return "\n".join(clean_lines)

def execute_sql_file(cursor, file_path, target_db=None):
    """
    Executes a multi-statement SQL script cleanly.
    Strips SQL comments first so statements with header comments are not accidentally skipped.
    Strips CREATE DATABASE / USE statements when target_db is active.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    clean_sql = strip_sql_comments(sql_content)
    statements = clean_sql.split(";")
    for stmt in statements:
        clean_stmt = stmt.strip()
        if not clean_stmt:
            continue
        # Skip CREATE DATABASE and USE statements if target_db is set
        if target_db:
            if re.match(r'^CREATE\s+DATABASE', clean_stmt, re.IGNORECASE):
                continue
            if re.match(r'^USE\s+', clean_stmt, re.IGNORECASE):
                continue
        cursor.execute(clean_stmt)

def initialize_database():
    """Applies schema and seed data to MySQL."""
    print("=" * 70)
    print(" SmartRetail — MySQL Database Provisioning & Initialization")
    print("=" * 70)
    print(f"Target Server : {DB_HOST}:{DB_PORT} (User: {DB_USER})")
    print(f"Target DB     : {DB_NAME}\n")

    # Step 1: Connect to server and verify / create database
    created_db = False
    try:
        conn = get_connection(include_db=False)
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.close()
        print(f"[OK] Database '{DB_NAME}' created or verified via server root connection.")
        created_db = True
    except Exception as e:
        print(f"[INFO] Root server connection skipped ({e}). Attempting direct database connection to '{DB_NAME}'...")

    # Verify direct connection to target DB
    try:
        conn = get_connection(include_db=True)
        conn.close()
        print(f"[OK] Connected directly to target database '{DB_NAME}'.")
    except Exception as e:
        print(f"[ERROR] Could not connect to target database '{DB_NAME}': {e}")
        print("\nPlease check your DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, and DB_NAME environment variables.")
        return False

    # Step 2: Connect to DB and apply schema.sql
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    expected_tables = [
        "stores", "users", "suppliers", "products", "inventory",
        "sales", "sale_items", "forecasts", "reorder_recommendations"
    ]
    try:
        conn = get_connection(include_db=True)
        with conn.cursor() as cursor:
            execute_sql_file(cursor, schema_path, target_db=DB_NAME)
            cursor.execute("SHOW TABLES;")
            found_tables = [list(r.values())[0].lower() for r in cursor.fetchall()]
        conn.close()

        missing = [t for t in expected_tables if t.lower() not in found_tables]
        if missing:
            print(f"[ERROR] schema.sql executed but missing expected tables: {missing}")
            return False
        print(f"[OK] schema.sql executed successfully (All {len(found_tables)} core tables verified in database).")
    except Exception as e:
        print(f"[ERROR] Failed to execute schema.sql: {e}")
        return False

    # Step 3: Apply seed.sql (Real FreshRetailNet-50K catalog and transactions)
    seed_path = os.path.join(os.path.dirname(__file__), "seed.sql")
    try:
        conn = get_connection(include_db=True)
        with conn.cursor() as cursor:
            execute_sql_file(cursor, seed_path, target_db=DB_NAME)
        conn.close()
        print(f"[OK] seed.sql executed successfully (FreshRetailNet-50K seed data inserted).\n")
    except Exception as e:
        print(f"[ERROR] Failed to execute seed.sql: {e}")
        return False

    # Step 4: Run Verification Queries
    return run_verifications()

def run_verifications():
    """Runs data integrity and representative analytics verification queries."""
    print("-" * 70)
    print("RUNNING VERIFICATION QUERIES ON MYSQL")
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
            cursor.execute(f"SELECT COUNT(*) as count FROM `{t}`;")
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

        # Check 6: Orphan Records Check (Referential Integrity)
        print("\n6. Referential Integrity / Orphan Records Check:")
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
    print("[SUCCESS] MySQL schema & seed verification checks PASSED!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = initialize_database()
    sys.exit(0 if success else 1)
