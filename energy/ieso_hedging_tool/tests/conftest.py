import pytest
from pathlib import Path

@pytest.fixture(autouse=True)
def mock_cache_dir(monkeypatch, tmp_path):
    """
    Override the default data/processed paths in the engines to use a temporary directory during testing.
    This prevents test data from polluting the real cache and ensures a clean state per test.
    """
    monkeypatch.setattr("src.engines.weather_engine._CACHE_DIR", tmp_path / "weather")
    monkeypatch.setattr("src.engines.ieso_engine._CACHE_DIR", tmp_path / "ieso")
