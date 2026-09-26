import pytest
import pymysql
from unittest.mock import MagicMock, patch
from app import create_app
from app.db import query_db, execute_db, check_db_health

@pytest.fixture
def app_context():
    app = create_app("testing")
    with app.app_context():
        yield app

def test_query_db_mocked(app_context):
    """Tests that query_db correctly executes parameterized SELECT and closes cursor."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [{"product_id": 1, "name": "Masala Chai"}]
    
    mock_db = MagicMock()
    mock_db.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("app.db.get_db", return_value=mock_db):
        results = query_db("SELECT * FROM products WHERE product_id = %s", (1,))
        assert len(results) == 1
        assert results[0]["name"] == "Masala Chai"
        mock_cursor.execute.assert_called_once_with("SELECT * FROM products WHERE product_id = %s", (1,))

def test_execute_db_commit(app_context):
    """Tests that execute_db commits valid write operations."""
    mock_cursor = MagicMock()
    mock_cursor.lastrowid = 42
    mock_cursor.rowcount = 1
    
    mock_db = MagicMock()
    mock_db.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("app.db.get_db", return_value=mock_db):
        res = execute_db("INSERT INTO stores (name) VALUES (%s)", ("Test Store",))
        assert res["lastrowid"] == 42
        assert res["rowcount"] == 1
        mock_db.commit.assert_called_once()

def test_execute_db_rollback_on_error(app_context):
    """Tests that execute_db automatically triggers rollback when an exception occurs."""
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = pymysql.MySQLError("Duplicate entry for key")
    
    mock_db = MagicMock()
    mock_db.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("app.db.get_db", return_value=mock_db):
        with pytest.raises(pymysql.MySQLError):
            execute_db("INSERT INTO users (username) VALUES (%s)", ("duplicate_user",))
        mock_db.rollback.assert_called_once()

def test_db_ssl_config_injection(app_context):
    """Tests that DB_SSL_MODE and DB_SSL_CA configure pymysql connection parameters properly."""
    from app.db import get_db, close_db
    from flask import g
    
    close_db()
    with patch("pymysql.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        with patch.dict(app_context.config, {"DB_SSL_MODE": "REQUIRED", "DB_SSL_CA": "/path/to/ca.pem"}):
            db = get_db()
            assert db is not None
            mock_connect.assert_called_once()
            call_kwargs = mock_connect.call_args[1]
            assert "ssl" in call_kwargs
            assert call_kwargs["ssl"]["ssl_mode"] == "REQUIRED"
            assert call_kwargs["ssl"]["ca"] == "/path/to/ca.pem"
    close_db()

def test_execute_sql_file_strips_hardcoded_use():
    """Tests that execute_sql_file skips CREATE DATABASE and USE statements when target_db is set."""
    from database.init_db import execute_sql_file
    import tempfile
    
    mock_cursor = MagicMock()
    with tempfile.NamedTemporaryFile("w+", suffix=".sql", delete=False, encoding="utf-8") as tf:
        tf.write("CREATE DATABASE IF NOT EXISTS smart_retail_db;\nUSE smart_retail_db;\nCREATE TABLE stores (id INT);\n")
        temp_path = tf.name
        
    try:
        execute_sql_file(mock_cursor, temp_path, target_db="custom_cloud_db")
        # Should only execute CREATE TABLE stores
        assert mock_cursor.execute.call_count == 1
        assert "CREATE TABLE stores" in mock_cursor.execute.call_args[0][0]
    finally:
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)

