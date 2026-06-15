import pytest
import numpy as np
from src.engines.nlswe import NLSWEParameters, initialize_state, compute_time_step, step_nlswe

def test_initialize_state():
    eta0 = np.array([[1.0, 1.0], [1.0, 1.0]])
    Z = np.array([[-5.0, -5.0], [-5.0, -5.0]])
    
    h, u, v = initialize_state(Z, eta0)
    
    assert np.allclose(h, 6.0)
    assert np.allclose(u, 0.0)
    assert np.allclose(v, 0.0)

def test_compute_time_step():
    X = np.array([[0, 10], [0, 10]])
    Y = np.array([[0, 0], [10, 10]])
    h = np.array([[5.0, 5.0], [5.0, 5.0]])
    params = NLSWEParameters(cfl=0.4, g=9.81)
    
    dt = compute_time_step(X, Y, h, params)
    
    assert dt > 0
    assert isinstance(dt, float)

def test_step_nlswe():
    # create a simple 3x3 grid
    x = np.linspace(0, 20, 3)
    y = np.linspace(0, 20, 3)
    X, Y = np.meshgrid(x, y)
    Z = np.full_like(X, -10.0)
    
    eta = np.zeros_like(X)
    eta[1, 1] = 2.0 # central bump
    
    h, u, v = initialize_state(Z, eta)
    
    params = NLSWEParameters(cfl=0.4, g=9.81)
    dt = compute_time_step(X, Y, h, params)
    
    eta_new, u_new, v_new = step_nlswe(eta, u, v, Z, X, Y, dt, params)
    
    assert eta_new.shape == eta.shape
    assert u_new.shape == u.shape
    assert v_new.shape == v.shape
