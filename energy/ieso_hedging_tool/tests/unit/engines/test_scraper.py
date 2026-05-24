import pytest
import pandas as pd
import requests
from unittest.mock import patch, MagicMock
from io import StringIO
from energy.ieso_hedging_tool.src.engines.scraper import fetch_ieso_data

def test_fetch_ieso_data_success():
    # Mock response for one day
    mock_csv = """Metadata Row
Pricing Location,LMP,Delivery Hour
ONTARIO_ZONAL_PRICE,35.5,1
ONTARIO_ZONAL_PRICE,36.0,2
OTHER_ZONE,40.0,1
"""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_csv
        mock_get.return_value = mock_response
        
        # Test for a single day to keep it simple (mocking a month would require many calls)
        # Actually fetch_ieso_data iterates over all days in a month.
        # I'll patch datetime to test a month with only 1 day if possible, or just let it run.
        # Testing 202301 (31 days) might be slow if not fully mocked.
        
        # To make it fast, I'll mock the loop or the date range.
        # For now, let's just mock requests.get to always return the same data.
        
        result = fetch_ieso_data("202301")
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert "Ontario Price" in result.columns
        assert result["Ontario Price"].iloc[0] == 35.5

def test_fetch_ieso_data_invalid_month():
    result = fetch_ieso_data("invalid")
    assert "Error parsing month" in result

def test_fetch_ieso_data_no_data():
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = fetch_ieso_data("202301")
        assert "Error: No data found" in result
