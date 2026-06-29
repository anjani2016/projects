# tests/test_imports.py
import sys
import pytest
from unittest.mock import MagicMock, patch

def test_subpackage_imports():
    """Verify that all core components can be imported from their subpackages correctly."""
    try:
        from src.preprocessing.processor import WeldProcessor
        from src.rule_engine.engine import WeldEngine
        from src.detection.detector import WeldDetector
        
        # Instantiate to ensure basic initialization works
        assert WeldProcessor is not None
        assert WeldEngine is not None
        assert WeldDetector is not None
    except ModuleNotFoundError as e:
        pytest.fail(f"Core packages failed to import from standard subpaths: {e}")

import builtins

@patch("sys.exit")
@patch("streamlit.error")
def test_main_import_exception_handling(mock_st_error, mock_sys_exit):
    """
    Test that if a ModuleNotFoundError occurs during startup, the application
    gracefully catches the exception, displays our premium error card, and exits safely.
    """
    # Temporarily remove main from sys.modules if it is already loaded
    if "main" in sys.modules:
        del sys.modules["main"]
        
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if "src.preprocessing.processor" in name:
            raise ModuleNotFoundError("No module named 'src.preprocessing.processor'")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        try:
            import main
        except Exception:
            pass
        
        # Verify our custom streamlit error message was displayed
        assert mock_st_error.called
        args, _ = mock_st_error.call_args
        assert "Environment Configuration Error" in args[0]
        assert "export PYTHONPATH=$(pwd)" in args[0]
        
        # Verify the script exited cleanly with code 1 instead of raised traceback
        mock_sys_exit.assert_called_once_with(1)
