"""
SmartRetail Database Layer
Provides safe, thread-local MySQL connection management with local SQLite fallback,
parameterized query execution, automatic transaction rollback on error, and teardown resource cleanup.
"""

import os
import re
import sqlite3
from datetime import datetime
import pandas as pd
import pymysql
import pymysql.cursors
from flask import current_app, g
import logging

logger = logging.getLogger(__name__)

def _get_sqlite_db_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "database", "smart_retail.db")

def _sqlite_dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def _adapt_sql_for_sqlite(sql):
    """Translates MySQL-specific syntax to SQLite syntax."""
    # Handle subquery date arithmetic: (SELECT ... FROM ...) - INTERVAL %s DAY
    adapted = re.sub(r'(\(SELECT[\s\S]*?FROM[\s\S]*?\))\s*-\s*INTERVAL\s+(%s|\?)\s+DAY', r"date(\1, '-' || ? || ' day')", sql, flags=re.IGNORECASE)
    # Handle INTERVAL with literal digits first
    adapted = re.sub(r'NOW\(\)\s*-\s*INTERVAL\s+(\d+)\s+DAY', r"datetime('now', '-\1 day')", adapted, flags=re.IGNORECASE)
    adapted = re.sub(r'CURDATE\(\)\s*-\s*INTERVAL\s+(\d+)\s+DAY', r"date('now', '-\1 day')", adapted, flags=re.IGNORECASE)
    # Handle INTERVAL with parameter placeholders (%s or ?)
    adapted = re.sub(r'NOW\(\)\s*-\s*INTERVAL\s+(%s|\?)\s+DAY', r"datetime('now', '-' || ? || ' day')", adapted, flags=re.IGNORECASE)
    adapted = re.sub(r'CURDATE\(\)\s*-\s*INTERVAL\s+(%s|\?)\s+DAY', r"date('now', '-' || ? || ' day')", adapted, flags=re.IGNORECASE)
    # Handle any remaining identifier - INTERVAL %s DAY
    adapted = re.sub(r'([a-zA-Z0-9_\.]+)\s*-\s*INTERVAL\s+(%s|\?)\s+DAY', r"date(\1, '-' || ? || ' day')", adapted, flags=re.IGNORECASE)
    # Replace remaining %s with ? for parameterized queries
    adapted = re.sub(r'(?<!%)(%s)', '?', adapted)
    return adapted



class SQLiteCursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor
        
    def execute(self, sql, params=None):
        adapted_sql = _adapt_sql_for_sqlite(sql)
        return self._cursor.execute(adapted_sql, params or ())
        
    def fetchone(self):
        return self._cursor.fetchone()
        
    def fetchall(self):
        return self._cursor.fetchall()
        
    def fetchmany(self, size=None):
        return self._cursor.fetchmany(size) if size else self._cursor.fetchmany()
        
    @property
    def lastrowid(self):
        return self._cursor.lastrowid
        
    @property
    def rowcount(self):
        return self._cursor.rowcount
        
    @property
    def description(self):
        return self._cursor.description
        
    def close(self):
        return self._cursor.close()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cursor.close()

class SQLiteConnWrapper:
    def __init__(self, conn):
        self._conn = conn
        
    def cursor(self):
        return SQLiteCursorWrapper(self._conn.cursor())
        
    def commit(self):
        return self._conn.commit()
        
    def rollback(self):
        return self._conn.rollback()
        
    def close(self):
        return self._conn.close()

def get_db():
    """
    Opens or retrieves a unique database connection for the current Flask request context.
    Attempts MySQL first; falls back to local SQLite if MySQL is unavailable.
    """
    if 'db' not in g:
        # Try MySQL connection first
        try:
            g.db = pymysql.connect(
                host=current_app.config['DB_HOST'],
                port=current_app.config['DB_PORT'],
                user=current_app.config['DB_USER'],
                password=current_app.config['DB_PASSWORD'],
                database=current_app.config['DB_NAME'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            g.db_type = 'mysql'
        except Exception as e:
            logger.warning(f"MySQL connection unavailable ({e}). Falling back to local SQLite database.")
            sqlite_path = _get_sqlite_db_path()
            conn = sqlite3.connect(sqlite_path)
            conn.row_factory = _sqlite_dict_factory
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.create_function("CURDATE", 0, lambda: datetime.now().strftime("%Y-%m-%d"))
            conn.create_function("NOW", 0, lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            conn.create_function("DATEDIFF", 2, lambda d1, d2: (pd.to_datetime(d1) - pd.to_datetime(d2)).days if d1 and d2 else None)
            g.db = SQLiteConnWrapper(conn)
            g.db_type = 'sqlite'

    return g.db


def close_db(e=None):
    """
    Closes the request's database connection during app context teardown.
    """
    db = g.pop('db', None)
    g.pop('db_type', None)
    if db is not None:
        try:
            db.close()
        except Exception as err:
            logger.warning(f"Error closing DB connection: {err}")

def query_db(sql, params=None, one=False):
    """
    Executes a SELECT query with parameterized inputs and returns dict records.
    """
    db = get_db()
    db_type = getattr(g, 'db_type', 'mysql')
    
    if db_type == 'sqlite':
        adapted_sql = _adapt_sql_for_sqlite(sql)
        cursor = db.cursor()
        try:
            cursor.execute(adapted_sql, params or ())
            result = cursor.fetchall()
            return (result[0] if result else None) if one else result
        finally:
            cursor.close()
    else:
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
    """
    db = get_db()
    db_type = getattr(g, 'db_type', 'mysql')
    
    if db_type == 'sqlite':
        adapted_sql = _adapt_sql_for_sqlite(sql)
        cursor = db.cursor()
        try:
            cursor.execute(adapted_sql, params or ())
            db.commit()
            return {
                "lastrowid": cursor.lastrowid,
                "rowcount": cursor.rowcount
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed and rolled back: {e} | SQL: {sql}")
            raise e
        finally:
            cursor.close()
    else:
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
    Performs a lightweight connectivity check against the configured database.
    Returns a dict with status and metadata (without sensitive credentials).
    """
    # If explicitly configured for sqlite or testing sqlite
    db_engine = current_app.config.get('DB_ENGINE', 'mysql')
    
    if db_engine == 'sqlite':
        try:
            sqlite_path = _get_sqlite_db_path()
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 AS ping;")
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            table_count = cursor.fetchone()[0]
            conn.close()
            return {
                "status": "connected",
                "database_name": "smart_retail_db (local SQLite)",
                "tables_found": table_count,
                "engine": "sqlite",
                "ping": True
            }
        except Exception as e:
            return {
                "status": "disconnected",
                "database_name": "smart_retail_db",
                "error": str(e)
            }
    
    # Check MySQL connectivity directly
    try:
        conn = pymysql.connect(
            host=current_app.config['DB_HOST'],
            port=current_app.config['DB_PORT'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            database=current_app.config['DB_NAME'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=3
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 AS ping;")
            ping = cursor.fetchone()
            cursor.execute("""
                SELECT COUNT(*) AS table_count 
                FROM information_schema.tables 
                WHERE table_schema = %s;
            """, (current_app.config['DB_NAME'],))
            res = cursor.fetchone()
            table_count = res['table_count'] if res else 0
        conn.close()
        return {
            "status": "connected",
            "database_name": current_app.config['DB_NAME'],
            "tables_found": table_count,
            "engine": "mysql",
            "ping": ping['ping'] == 1
        }
    except Exception as e:
        # If MySQL is not reachable, check if SQLite fallback is available locally
        sqlite_path = _get_sqlite_db_path()
        if os.path.exists(sqlite_path) and current_app.config.get('DB_HOST') in ('localhost', '127.0.0.1'):
            try:
                conn = sqlite3.connect(sqlite_path)
                cursor = conn.cursor()
                cursor.execute("SELECT 1 AS ping;")
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                table_count = cursor.fetchone()[0]
                conn.close()
                return {
                    "status": "connected",
                    "database_name": "smart_retail_db (local SQLite fallback)",
                    "tables_found": table_count,
                    "engine": "sqlite_fallback",
                    "ping": True
                }
            except Exception:
                pass
        
        return {
            "status": "disconnected",
            "database_name": current_app.config.get('DB_NAME', 'unknown'),
            "error": str(e)
        }


def init_app(app):
    """
    Registers teardown handlers with the Flask app factory.
    """
    app.teardown_appcontext(close_db)

