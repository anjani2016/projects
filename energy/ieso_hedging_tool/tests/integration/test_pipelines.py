import pytest
import os
import shutil
from pathlib import Path
from energy.ieso_hedging_tool.src.engines.ieso_engine import (
    fetch_historical_grid_matrix,
    _year_cache_path,
    _META_FILE,
    delete_year_cache_ieso
)

@pytest.fixture(autouse=True)
def clean_cache():
    """Ensure a clean cache for each test."""
    # Since we can't easily change the cache dir globally without refactoring,
    # we'll manually clean up the years we use.
    test_years = [1990, 1991]
    for y in test_years:
        delete_year_cache_ieso(y)
    yield
    for y in test_years:
        delete_year_cache_ieso(y)

def test_ieso_caching_pipeline():
    # 1. Fetch data for a year that isn't cached (should trigger synthetic generation)
    year = 1990
    df = fetch_historical_grid_matrix(year, year)
    
    assert not df.empty
    assert os.path.exists(_year_cache_path(year))
    
    # 2. Verify it's in the metadata
    import json
    with open(_META_FILE, "r") as f:
        meta = json.load(f)
    assert str(year) in meta
    assert meta[str(year)]["source"] == "synthetic"
    
    # 3. Fetch again, should load from cache (fast)
    df_cached = fetch_historical_grid_matrix(year, year)
    assert len(df_cached) == len(df)
