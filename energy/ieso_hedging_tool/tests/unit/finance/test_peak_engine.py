import pytest
import pandas as pd
import numpy as np
from energy.ieso_hedging_tool.src.finance.peak_engine import PeakMitigationEngine

@pytest.fixture
def sample_data():
    ts = pd.to_datetime(["2023-01-01 12:00:00", "2023-01-01 13:00:00"])
    df_client = pd.DataFrame({
        "timestamp": ts,
        "client_kw": [5000, 6000]
    })
    df_ieso_peaks = pd.DataFrame({
        "timestamp": ts,
        "ieso_system_mw": [20000, 21000],
        "peak_rank": [1, 2]
    })
    return df_client, df_ieso_peaks

def test_peak_mitigation_engine_simulation(sample_data):
    df_client, df_ieso_peaks = sample_data
    engine = PeakMitigationEngine(total_ga_pool=3_000_000_000)
    
    result = engine.simulate_mitigation(
        df_client=df_client,
        df_ieso_peaks=df_ieso_peaks,
        curtailment_kw=1000,
        battery_kw=500,
        battery_kwh=500
    )
    
    assert "event_breakdown" in result
    assert "summary" in result
    assert len(result["event_breakdown"]) == 2
    
    summary = result["summary"]
    assert summary["original_ga_cost"] > summary["mitigated_ga_cost"]
    assert summary["total_savings"] > 0

def test_peak_mitigation_engine_no_peaks(sample_data):
    df_client, df_ieso_peaks = sample_data
    # Use different timestamps for peaks so they don't match
    df_ieso_peaks["timestamp"] = pd.to_datetime(["2023-02-01 12:00:00", "2023-02-01 13:00:00"])
    
    engine = PeakMitigationEngine()
    result = engine.simulate_mitigation(
        df_client=df_client,
        df_ieso_peaks=df_ieso_peaks,
        curtailment_kw=1000,
        battery_kw=500,
        battery_kwh=500
    )
    
    assert len(result["event_breakdown"]) == 0
    assert result["summary"]["total_savings"] == 0
