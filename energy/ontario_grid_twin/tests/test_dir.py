import os
import pytest


def test_data_paths_exist():
    """
    This is a Unit Test. It checks if the required directories 
    exist before we even try to run the app.
    """
    required_paths = [
        'data/processed/analyzed_substations.parquet',
        'data/raw/generation_sources.parquet',
        'data/raw/existing_dc.parquet'
    ]
    for path in required_paths:
        assert os.path.exists(path) == True, f"Missing critical file: {path}"