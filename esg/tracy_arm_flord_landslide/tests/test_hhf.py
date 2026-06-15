import pytest
import numpy as np
from src.engines.hhf import SlideParameters, WaterColumnParameters, compute_impulse_parameter, compute_initial_wave_amplitude, apply_eta0_to_mesh

def test_compute_impulse_parameter():
    slide = SlideParameters(
        volume=1000.0,
        mass=2000000.0,
        impact_velocity=20.0,
        thickness=10.0,
        width=50.0,
        impact_angle_deg=45.0
    )
    water = WaterColumnParameters(
        depth_at_impact=50.0,
        density=1000.0,
        g=9.81
    )
    
    P = compute_impulse_parameter(slide, water)
    assert P > 0
    assert isinstance(P, float)

def test_compute_initial_wave_amplitude():
    slide = SlideParameters(
        volume=1000.0,
        mass=2000000.0,
        impact_velocity=20.0,
        thickness=10.0,
        width=50.0,
        impact_angle_deg=45.0
    )
    water = WaterColumnParameters(
        depth_at_impact=50.0,
        density=1000.0,
        g=9.81
    )
    
    amp = compute_initial_wave_amplitude(slide, water)
    assert amp > 0
    assert isinstance(amp, float)

def test_apply_eta0_to_mesh():
    x = np.linspace(0, 100, 10)
    y = np.linspace(0, 100, 10)
    X, Y = np.meshgrid(x, y)
    Z = np.full_like(X, -50.0) # all water
    
    slide = SlideParameters(
        volume=1000.0,
        mass=2000000.0,
        impact_velocity=20.0,
        thickness=10.0,
        width=50.0,
        impact_angle_deg=45.0
    )
    water = WaterColumnParameters(
        depth_at_impact=50.0,
        density=1000.0,
        g=9.81
    )
    
    eta0 = apply_eta0_to_mesh(X, Y, Z, impact_center=(50.0, 50.0), slide=slide, water=water, radius=10.0)
    
    assert eta0.shape == X.shape
    assert np.max(eta0) > 0
