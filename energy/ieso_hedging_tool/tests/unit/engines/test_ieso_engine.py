import pytest
from energy.ieso_hedging_tool.src.engines.ieso_engine import (
    generate_synthetic_year_ieso,
    load_cache_meta_ieso,
    fetch_historical_grid_matrix
)

def test_generate_synthetic_ieso_year():
    """Test generating synthetic IESO demand and price data."""
    year = 2021
    generate_synthetic_year_ieso(year)
    
    # Check metadata reflects synthetic cache
    meta = load_cache_meta_ieso()
    assert str(year) in meta
    assert meta[str(year)]["source"] == "synthetic"
    
    # Retrieve data
    df = fetch_historical_grid_matrix(year, year)
    assert not df.empty
    assert len(df) in [8760, 8784]  # Hourly data for a standard or leap year
    assert "Ontario Demand" in df.columns
    assert "Market_Price" in df.columns
    
    # Check structural boundaries
    assert df["Ontario Demand"].min() > 8000
    assert df["Market_Price"].max() > 0
