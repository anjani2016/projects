import pytest
import os
import sqlite3
import pandas as pd
from energy.ieso_hedging_tool.src.core.db_manager import DatabaseManager

@pytest.fixture
def db_manager(tmp_path):
    db_file = tmp_path / "test.db"
    return DatabaseManager(db_path=str(db_file))

def test_db_initialization(db_manager):
    # Connect once to ensure the file is created for SQLite
    with db_manager.get_connection() as conn:
        pass
    assert os.path.exists(db_manager.db_path)

def test_execute_query(db_manager):
    query = "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)"
    db_manager.execute_query(query)
    
    insert_query = "INSERT INTO test_table (name) VALUES (?)"
    last_id = db_manager.execute_query(insert_query, ("Alice",))
    assert last_id == 1

def test_fetch_dataframe(db_manager):
    db_manager.execute_query("CREATE TABLE test_table (id INTEGER PRIMARY KEY, value REAL)")
    db_manager.execute_query("INSERT INTO test_table (value) VALUES (?)", (10.5,))
    db_manager.execute_query("INSERT INTO test_table (value) VALUES (?)", (20.0,))
    
    df = db_manager.fetch_dataframe("SELECT * FROM test_table")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert df["value"].iloc[0] == 10.5

def test_get_connection_rollback(db_manager):
    db_manager.execute_query("CREATE TABLE test_table (id INTEGER PRIMARY KEY)")
    
    with pytest.raises(sqlite3.Error):
        with db_manager.get_connection() as conn:
            conn.execute("INSERT INTO test_table (id) VALUES (1)")
            conn.execute("INSERT INTO test_table (id) VALUES (1)")  # Should fail (duplicate ID)
    
    # Check if first insert was rolled back
    df = db_manager.fetch_dataframe("SELECT * FROM test_table")
    assert len(df) == 0
