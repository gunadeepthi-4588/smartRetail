"""
SmartRetail Database Layer
Provides safe, thread-local MySQL connection management, parameterized query execution,
automatic transaction rollback on error, and teardown resource cleanup.
"""

import pymysql
import pymysql.cursors
from flask import current_app, g
import logging

logger = logging.getLogger(__name__)

def get_db():
    """
    Opens or retrieves a unique MySQL connection for the current Flask request context.
    The connection is cached on Flask's 'g' object and closed automatically on request teardown.
    """
    if 'db' not in g:
        try:
            g.db = pymysql.connect(
                host=current_app.config['DB_HOST'],
                port=current_app.config['DB_PORT'],
                user=current_app.config['DB_USER'],
                password=current_app.config['DB_PASSWORD'],
                database=current_app.config['DB_NAME'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False  # Explicit transaction management
            )
        except pymysql.MySQLError as e:
            logger.error(f"Database connection error: {e}")
            raise e
    return g.db

def close_db(e=None):
    """
    Closes the request's MySQL connection during app context teardown.
    """
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception as err:
            logger.warning(f"Error closing DB connection: {err}")

def query_db(sql, params=None, one=False):
    """
    Executes a SELECT query with parameterized inputs and returns dict records.
    Safely closes the cursor after execution.
    """
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(sql, params or ())
            result = cursor.fetchall()
            return (result[0] if result else None) if one else result
    except pymysql.MySQLError as e:
        logger.error(f"Query execution error: {e} | SQL: {sql}")
        raise e

def execute_db(sql, params=None):
    """
    Executes an INSERT, UPDATE, or DELETE query within a transaction.
    Commits on success; rolls back automatically on error.
    Returns: dict with 'lastrowid' and 'rowcount'.
    """
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(sql, params or ())
            db.commit()
            return {
                "lastrowid": cursor.lastrowid,
                "rowcount": cursor.rowcount
            }
    except pymysql.MySQLError as e:
        db.rollback()
        logger.error(f"Transaction failed and rolled back: {e} | SQL: {sql}")
        raise e

def check_db_health():
    """
    Performs a lightweight connectivity check against MySQL.
    Returns a dict with status and metadata (without sensitive credentials).
    """
    try:
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT 1 AS ping;")
            ping = cursor.fetchone()
            
            # Count existing tables in the database
            cursor.execute("""
                SELECT COUNT(*) AS table_count 
                FROM information_schema.tables 
                WHERE table_schema = %s;
            """, (current_app.config['DB_NAME'],))
            res = cursor.fetchone()
            table_count = res['table_count'] if res else 0

        return {
            "status": "connected",
            "database_name": current_app.config['DB_NAME'],
            "tables_found": table_count,
            "ping": ping['ping'] == 1
        }
    except Exception as e:
        db_name = "unknown"
        if current_app:
            db_name = current_app.config.get('DB_NAME', 'unknown')
        return {
            "status": "disconnected",
            "database_name": db_name,
            "error": str(e)
        }

def init_app(app):
    """
    Registers teardown handlers with the Flask app factory.
    """
    app.teardown_appcontext(close_db)
