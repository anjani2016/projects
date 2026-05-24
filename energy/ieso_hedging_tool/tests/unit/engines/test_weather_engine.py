import pytest
import pandas as pd
from energy.ieso_hedging_tool.src.engines.weather_engine import (
    generate_synthetic_year,
    load_cache_meta,
    fetch_daily_weather,
    fetch_multi_year_weather
)

def test_generate_synthetic_weather_year():
    """Test generating and saving a synthetic weather year."""
    year = 2021
    generate_synthetic_year(year)
    
    # Check meta updated
    meta = load_cache_meta()
    assert str(year) in meta
    assert meta[str(year)]["source"] == "synthetic"
    
    # Check daily data retrieval
    df = fetch_daily_weather(year, year)
    assert not df.empty
    assert len(df) in [365, 366]  # Number of days in a year
    assert "Temperature" in df.columns
    assert df["Temperature"].min() >= -20
    assert df["Temperature"].max() <= 40

def test_fetch_multi_year_weather_aggregation():
    """Test that multi-year aggregates daily into weekly means."""
    generate_synthetic_year(2022)
    df_weekly = fetch_multi_year_weather(2022, 2022)
    
    assert not df_weekly.empty
    assert "Week" in df_weekly.columns
    # A year has 52 or 53 ISO weeks
    assert len(df_weekly) in [52, 53]
