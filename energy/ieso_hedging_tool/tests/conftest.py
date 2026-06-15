import sys
import os
import pytest
from pathlib import Path

# Ensure parent directory of 'energy' is in sys.path for test imports
current_dir = os.path.dirname(os.path.abspath(__file__))
grandparent_dir = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if grandparent_dir not in sys.path:
    sys.path.insert(0, grandparent_dir)

@pytest.fixture(autouse=True)
def mock_cache_dir(monkeypatch, tmp_path):
    """
    Override the default data/processed paths in the engines to use a temporary directory during testing.
    This prevents test data from polluting the real cache and ensures a clean state per test.
    """
    monkeypatch.setattr("src.engines.weather_engine._CACHE_DIR", tmp_path / "weather")
    monkeypatch.setattr("src.engines.ieso_engine._CACHE_DIR", tmp_path / "ieso")
