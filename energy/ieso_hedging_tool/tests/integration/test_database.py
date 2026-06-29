import pytest
import os
import pandas as pd
from energy.ieso_hedging_tool.src.core.db_manager import DatabaseManager

@pytest.fixture
def db_manager(tmp_path):
    db_file = tmp_path / "integration_test.db"
    return DatabaseManager(db_path=str(db_file))

def test_database_lifecycle(db_manager):
    # 1. Create table
    db_manager.execute_query("CREATE TABLE hourly_data (timestamp DATETIME, value REAL)")
    
    # 2. Insert data
    db_manager.execute_query("INSERT INTO hourly_data (timestamp, value) VALUES (?, ?)", ("2023-01-01 00:00:00", 100.5))
    
    # 3. Fetch as dataframe
    df = db_manager.fetch_dataframe("SELECT * FROM hourly_data")
    assert len(df) == 1
    assert df["value"].iloc[0] == 100.5
    
    # 4. Bulk insert via dataframe (simulating a pipeline)
    df_new = pd.DataFrame({
        "timestamp": ["2023-01-01 01:00:00", "2023-01-01 02:00:00"],
        "value": [110.0, 120.0]
    })
    
    with db_manager.get_connection() as conn:
        df_new.to_sql("hourly_data", conn, if_exists="append", index=False)
        
    df_all = db_manager.fetch_dataframe("SELECT * FROM hourly_data")
    assert len(df_all) == 3
