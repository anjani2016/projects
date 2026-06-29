import pytest
import pandas as pd
import geopandas as gpd
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Ensure src is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.data_loader import load_infrastructure_data, load_geodata

@patch('src.engine.data_loader.Path.exists')
@patch('src.engine.data_loader.pd.read_csv')
def test_load_infrastructure_data_success(mock_read_csv, mock_exists):
    # Clear streamlit cache
    load_infrastructure_data.clear()
    
    # Setup mock
    mock_exists.return_value = True
    mock_df = pd.DataFrame({
        'infrastructure_cost': [100, 200, 50]
    })
    mock_read_csv.return_value = mock_df
    
    # Run function
    df = load_infrastructure_data()
    
    # Assertions
    assert not df.empty
    assert 'normalized_cost' in df.columns
    assert df['normalized_cost'].tolist() == [0.5, 1.0, 0.25]

@patch('src.engine.data_loader.Path.exists')
def test_load_infrastructure_data_not_found(mock_exists):
    # Clear streamlit cache
    load_infrastructure_data.clear()
    
    mock_exists.return_value = False
    
    df = load_infrastructure_data()
    
    assert df.empty

def test_load_geodata_success():
    load_geodata.clear()
    df = pd.DataFrame({
        'latitude': [34.0522, 36.1699],
        'longitude': [-118.2437, -115.1398],
        'city': ['Los Angeles', 'Las Vegas']
    })
    
    gdf = load_geodata(df)
    
    assert not gdf.empty
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf.crs == "EPSG:4326"
    assert len(gdf) == 2

def test_load_geodata_empty_or_invalid():
    load_geodata.clear()
    # Empty df
    df_empty = pd.DataFrame()
    gdf = load_geodata(df_empty)
    assert gdf.empty
    
    # Missing columns
    df_invalid = pd.DataFrame({'city': ['Los Angeles']})
    gdf = load_geodata(df_invalid)
    assert gdf.empty
