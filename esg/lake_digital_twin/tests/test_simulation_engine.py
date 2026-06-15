import pytest
from models.simulation_engine import run_lake_simulation, interpret_simulation

def test_run_lake_simulation():
    risk_prob, df_results = run_lake_simulation(40, 1.0, iterations=10)
    assert 0 <= risk_prob <= 100
    assert "Simulated_SI" in df_results.columns
    assert len(df_results) == 10

def test_interpret_simulation():
    import pandas as pd
    # Test excellent
    status, sum_str = interpret_simulation(0, pd.DataFrame({"Simulated_SI": [1.0, 2.0]}))
    assert status == "Excellent"
    
    # Test stable
    status, sum_str = interpret_simulation(3.0, pd.DataFrame({"Simulated_SI": [1.0, 2.0]}))
    assert status == "Stable"

    # Test caution
    status, sum_str = interpret_simulation(10.0, pd.DataFrame({"Simulated_SI": [-1.0, 2.0]}))
    assert status == "Caution"

    # Test High Risk
    status, sum_str = interpret_simulation(50.0, pd.DataFrame({"Simulated_SI": [-1.0, -2.0]}))
    assert status == "High Risk"
