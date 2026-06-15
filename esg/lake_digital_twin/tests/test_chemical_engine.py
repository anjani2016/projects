import pytest
from models.chemical_engine import calculate_saturation_index, simulate_lake_stability, virtual_jar_test

def test_calculate_saturation_index():
    si = calculate_saturation_index(7.5, 50, 0.5)
    assert isinstance(si, float)

def test_simulate_lake_stability():
    status, color = simulate_lake_stability(0.5, 50)
    assert status == "Stable (Self-Buffering)"
    assert color == "green"
    
    status, color = simulate_lake_stability(2, 50)
    assert status == "Sensitive"
    assert color == "orange"
    
    status, color = simulate_lake_stability(5, 50)
    assert status == "Unstable (High Bloom Risk)"
    assert color == "red"

def test_virtual_jar_test():
    final_tp, removal_rate = virtual_jar_test(10.0, 50.0, 8.0)
    assert 0 <= final_tp <= 10.0
    assert 0 <= removal_rate <= 100.0
