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
