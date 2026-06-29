import pytest
import os
import logging
from energy.ieso_hedging_tool.src.core.utils import setup_logger, initialize_project, format_currency

def test_setup_logger():
    """Test that logger is set up correctly."""
    logger = setup_logger()
    assert logger.name == "ieso_hedging_tool"
    assert len(logger.handlers) >= 1
    # Check if log file is created
    assert os.path.exists("logs/project_log.txt")

def test_initialize_project():
    """Test that project folders are created."""
    initialize_project()
    folders = [
        'data/raw', 
        'data/processed', 
        'data/assets', 
        'logs'
    ]
    for folder in folders:
        assert os.path.exists(folder)

def test_format_currency():
    """Test currency formatting."""
    assert format_currency(1234.567) == "$1,234.57"
    assert format_currency(0) == "$0.00"
    assert format_currency(-100) == "$-100.00"
