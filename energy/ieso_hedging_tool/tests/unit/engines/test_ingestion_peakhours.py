import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from energy.ieso_hedging_tool.src.engines.ingestion_peakhours import fetch_live_ieso_demand

def test_fetch_live_ieso_demand_success():
    fetch_live_ieso_demand.clear()
    mock_csv = """H1
H2
H3
Date,Hour,Interval,Ontario Demand,Z1,Z2,Z3,Z4,Z5,Z6,Z7,Z8,Z9,Z10,Zones Total,DIFF
2023-01-01,1,1,15000,0,0,0,0,0,0,0,0,0,0,0,0
2023-01-01,1,2,15100,0,0,0,0,0,0,0,0,0,0,0,0
2023-01-01,2,1,16000,0,0,0,0,0,0,0,0,0,0,0,0
"""
    # Create the dataframe BEFORE patching
    df_mock = pd.read_csv(StringIO(mock_csv), skiprows=3)
    
    with patch('pandas.read_csv') as mock_read_csv:
        mock_read_csv.return_value = df_mock
        
        result = fetch_live_ieso_demand()
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2 # 2 hours
        assert "Ontario Demand" in result.columns
        assert result["Ontario Demand"].max() == 16000

def test_fetch_live_ieso_demand_failure():
    fetch_live_ieso_demand.clear()
    with patch('pandas.read_csv') as mock_read_csv:
        mock_read_csv.side_effect = Exception("Network error")
        
        result = fetch_live_ieso_demand()
        assert result.empty
from io import StringIO
