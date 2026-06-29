import pytest
import pandas as pd
from energy.ieso_hedging_tool.src.finance.peak_engine import PeakMitigationEngine

def test_peak_load_crash_empty_dataframe():
    """
    Regression test for a bug where simulate_mitigation crashed on empty input.
    """
    engine = PeakMitigationEngine()
    
    # Empty client data
    df_client = pd.DataFrame(columns=["timestamp", "client_kw"])
    # Empty IESO peaks
    df_ieso_peaks = pd.DataFrame(columns=["timestamp", "ieso_system_mw", "peak_rank"])
    
    # Should not crash and return a valid summary with zeros
    result = engine.simulate_mitigation(
        df_client=df_client,
        df_ieso_peaks=df_ieso_peaks,
        curtailment_kw=100,
        battery_kw=100,
        battery_kwh=100
    )
    
    assert result["summary"]["total_savings"] == 0.0
    assert result["event_breakdown"].empty
