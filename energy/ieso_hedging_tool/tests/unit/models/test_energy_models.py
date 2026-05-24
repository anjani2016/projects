import pytest
import numpy as np
from energy.ieso_hedging_tool.src.finance.models import EnergySimulator, PriceSimulator_static

def test_energy_simulator_initialization():
    sim = EnergySimulator(s0=30, mu=35, theta=0.1, sigma=5)
    assert sim.s0 == 30
    assert sim.mu == 35
    assert sim.theta == 0.1
    assert sim.sigma == 5

def test_energy_simulator_run():
    sim = EnergySimulator(s0=30, mu=35, theta=0.1, sigma=5)
    prices = sim.run_monte_carlo(n_steps=10)
    assert len(prices) == 10
    assert prices[0] == 30

def test_price_simulator_static():
    prices = PriceSimulator_static.simulate_ou(s0=30, mu=35, theta=0.1, sigma=5, n_steps=10)
    assert len(prices) == 10
    assert prices[0] == 30

def test_ou_reversion_trend():
    # If s0 << mu, prices should generally increase
    sim = EnergySimulator(s0=0, mu=100, theta=0.5, sigma=0.1) # low noise
    prices = sim.run_monte_carlo(n_steps=100)
    assert prices[-1] > prices[0]
    assert prices[-1] < 110 # Should be near mu
