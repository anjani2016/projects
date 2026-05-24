import pytest
from energy.ieso_hedging_tool.src.finance.finance import calculate_energy_greeks, calculate_ga_cost

def test_calculate_energy_greeks_call():
    result = calculate_energy_greeks(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type="call")
    assert "Premium" in result
    assert result["Premium"] > 0
    assert result["Delta"] > 0
    assert result["Gamma"] > 0
    assert result["Vega"] > 0

def test_calculate_energy_greeks_put():
    result = calculate_energy_greeks(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type="put")
    assert "Premium" in result
    assert result["Premium"] > 0
    assert result["Delta"] < 0

def test_calculate_energy_greeks_expiry():
    # At expiry
    result = calculate_energy_greeks(S=110, K=100, T=0, r=0.05, sigma=0.2, option_type="call")
    assert result["Premium"] == 10.0
    assert result["Delta"] == 1.0

def test_calculate_ga_cost_class_b():
    assert calculate_ga_cost(mwh=100, ga_class="B", rate_b=60.0) == 6000.0

def test_calculate_ga_cost_class_a():
    # Class A logic uses pdf * monthly_ga_pool
    # monthly_ga_pool is hardcoded as 1.2e9 in finance.py
    pdf = 0.001 # 0.1% of peak
    expected = 0.001 * 1.2e9
    assert calculate_ga_cost(mwh=100, ga_class="A", pdf=pdf) == expected
