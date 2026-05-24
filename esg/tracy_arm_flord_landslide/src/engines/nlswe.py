"""
nlswe.py (version1)

Non-linear Shallow Water Equations (NLSWE) solver.
Consumes:
- Mesh (X, Y, Z)
- Initial η0 field
Produces:
- Time-evolving η, u, v fields
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import numpy as np


# ---------------------------------------------------------
# Parameters
# ---------------------------------------------------------

@dataclass
class NLSWEParameters:
    g: float = 9.81
    manning_n: float = 0.025
    cfl: float = 0.4
    min_depth: float = 0.1


# ---------------------------------------------------------
# Initialization
# ---------------------------------------------------------

def initialize_state(Z: np.ndarray, eta0: np.ndarray):
    """Initialize water depth and velocities."""
    h = np.maximum(eta0 - Z, 0.0)
    u = np.zeros_like(h)
    v = np.zeros_like(h)
    return h, u, v


def compute_time_step(X: np.ndarray, Y: np.ndarray, h: np.ndarray, params: NLSWEParameters) -> float:
    """Compute stable dt using CFL condition."""
    dx = np.mean(np.diff(X[0, :]))
    dy = np.mean(np.diff(Y[:, 0]))
    c = np.sqrt(params.g * np.maximum(h, params.min_depth))
    return params.cfl * min(dx, dy) / (np.max(c) + 1e-6)


# ---------------------------------------------------------
# Single Time Step
# ---------------------------------------------------------

def step_nlswe(
    eta: np.ndarray,
    u: np.ndarray,
    v: np.ndarray,
    Z: np.ndarray,
    X: np.ndarray,
    Y: np.ndarray,
    dt: float,
    params: NLSWEParameters
):
    """Perform one explicit NLSWE step (simplified)."""
    g = params.g
    n = params.manning_n
    min_depth = params.min_depth

    dx = np.mean(np.diff(X[0, :]))
    dy = np.mean(np.diff(Y[:, 0]))

    h = np.maximum(eta - Z, min_depth)

    eta_new = eta.copy()
    u_new = u.copy()
    v_new = v.copy()

    i = slice(1, -1)
    j = slice(1, -1)

    # Derivatives
    d_eta_dx = (eta[i, j+1] - eta[i, j-1]) / (2 * dx)
    d_eta_dy = (eta[i+1, j] - eta[i-1, j]) / (2 * dy)

    d_uh_dx = ((u[i, j+1] * h[i, j+1]) - (u[i, j-1] * h[i, j-1])) / (2 * dx)
    d_vh_dy = ((v[i+1, j] * h[i+1, j]) - (v[i-1, j] * h[i-1, j])) / (2 * dy)

    # Continuity
    eta_new[i, j] = eta[i, j] - dt * (d_uh_dx + d_vh_dy)

    # Momentum
    Sf_x = n**2 * u[i, j] * np.sqrt(u[i, j]**2 + v[i, j]**2) / (h[i, j]**(4/3))
    Sf_y = n**2 * v[i, j] * np.sqrt(u[i, j]**2 + v[i, j]**2) / (h[i, j]**(4/3))

    u_new[i, j] = u[i, j] - dt * (g * d_eta_dx + g * Sf_x)
    v_new[i, j] = v[i, j] - dt * (g * d_eta_dy + g * Sf_y)

    return eta_new, u_new, v_new


# ---------------------------------------------------------
# Simulation Driver
# ---------------------------------------------------------

def run_simulation(
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
    eta0: np.ndarray,
    params: NLSWEParameters,
    t_final: float,
    output_interval: float
):
    """
    Generator that yields (t, eta, u, v) at each output interval.
    """
    eta = eta0.copy()
    h, u, v = initialize_state(Z, eta0)

    t = 0.0
    next_output = 0.0

    while t < t_final:
        dt = compute_time_step(X, Y, h, params)
        if t + dt > t_final:
            dt = t_final - t

        eta, u, v = step_nlswe(eta, u, v, Z, X, Y, dt, params)
        h = np.maximum(eta - Z, params.min_depth)
        t += dt

        if t >= next_output:
            yield t, eta.copy(), u.copy(), v.copy()
            next_output += output_interval
