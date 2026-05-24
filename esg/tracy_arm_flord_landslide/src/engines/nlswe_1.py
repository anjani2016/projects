"""
nlswe.py

Non-linear Shallow Water Equations (NLSWE) solver for
landslide-generated impulse waves in Tracy Arm Fjord.

This is a minimal, explicit finite-difference skeleton that:
- Consumes the mesh (X, Y, Z)
- Evolves free-surface elevation η and depth-averaged velocities (u, v)
- Can be extended with better numerics (e.g., MacCormack, TVD schemes)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass
class NLSWEParameters:
    g: float = 9.81          # gravity (m/s^2)
    manning_n: float = 0.025 # bottom friction coefficient
    cfl: float = 0.4         # CFL number for stability
    min_depth: float = 0.1   # minimum water depth to avoid division by zero


def initialize_state(
    Z: np.ndarray,
    eta0: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Initialize water depth and velocities.

    Parameters
    ----------
    Z : np.ndarray
        Bathymetry (negative below sea level).
    eta0 : np.ndarray
        Initial free-surface elevation.

    Returns
    -------
    h : np.ndarray
        Initial water depth.
    u : np.ndarray
        Initial x-velocity (zeros).
    v : np.ndarray
        Initial y-velocity (zeros).
    """
    h = np.maximum(eta0 - Z, 0.0)
    u = np.zeros_like(h)
    v = np.zeros_like(h)
    return h, u, v


def compute_time_step(
    X: np.ndarray,
    Y: np.ndarray,
    h: np.ndarray,
    params: NLSWEParameters
) -> float:
    """
    Compute stable time step based on CFL condition.

    Parameters
    ----------
    X, Y : np.ndarray
        Mesh coordinates.
    h : np.ndarray
        Water depth.
    params : NLSWEParameters

    Returns
    -------
    dt : float
        Time step (s).
    """
    g = params.g
    min_depth = params.min_depth

    # Grid spacing (assumes uniform)
    dx = np.mean(np.diff(X[0, :]))
    dy = np.mean(np.diff(Y[:, 0]))

    c = np.sqrt(g * np.maximum(h, min_depth))
    max_c = np.max(c)

    dt = params.cfl * min(dx, dy) / (max_c + 1e-6)
    return dt


def step_nlswe(
    eta: np.ndarray,
    u: np.ndarray,
    v: np.ndarray,
    Z: np.ndarray,
    X: np.ndarray,
    Y: np.ndarray,
    dt: float,
    params: NLSWEParameters
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Perform a single explicit time step of the NLSWE.

    This is a very simple, non-TVD, non-diffusive scheme intended
    as a starting point. It should be refined for production use.

    Parameters
    ----------
    eta, u, v : np.ndarray
        Current free-surface elevation and velocities.
    Z : np.ndarray
        Bathymetry.
    X, Y : np.ndarray
        Mesh coordinates.
    dt : float
        Time step.
    params : NLSWEParameters

    Returns
    -------
    eta_new, u_new, v_new : np.ndarray
        Updated state.
    """
    g = params.g
    min_depth = params.min_depth
    n = params.manning_n

    dx = np.mean(np.diff(X[0, :]))
    dy = np.mean(np.diff(Y[:, 0]))

    h = np.maximum(eta - Z, min_depth)

    # Pre-allocate
    eta_new = eta.copy()
    u_new = u.copy()
    v_new = v.copy()

    # Interior indices (ignore boundaries for now)
    i = slice(1, -1)
    j = slice(1, -1)

    # Derivatives (central differences)
    d_eta_dx = (eta[i, j+1] - eta[i, j-1]) / (2 * dx)
    d_eta_dy = (eta[i+1, j] - eta[i-1, j]) / (2 * dy)

    d_uh_dx = ( (u[i, j+1] * h[i, j+1]) - (u[i, j-1] * h[i, j-1]) ) / (2 * dx)
    d_vh_dy = ( (v[i+1, j] * h[i+1, j]) - (v[i-1, j] * h[i-1, j]) ) / (2 * dy)

    # Continuity: dη/dt + d(uh)/dx + d(vh)/dy = 0
    eta_new[i, j] = eta[i, j] - dt * (d_uh_dx + d_vh_dy)

    # Momentum (very simplified, no Coriolis, simple friction)
    d_u_dx = (u[i, j+1] - u[i, j-1]) / (2 * dx)
    d_u_dy = (u[i+1, j] - u[i-1, j]) / (2 * dy)

    d_v_dx = (v[i, j+1] - v[i, j-1]) / (2 * dx)
    d_v_dy = (v[i+1, j] - v[i-1, j]) / (2 * dy)

    # Friction term (Manning)
    Sf_x = n**2 * u[i, j] * np.sqrt(u[i, j]**2 + v[i, j]**2) / (h[i, j]**(4.0 / 3.0))
    Sf_y = n**2 * v[i, j] * np.sqrt(u[i, j]**2 + v[i, j]**2) / (h[i, j]**(4.0 / 3.0))

    u_new[i, j] = u[i, j] - dt * (u[i, j] * d_u_dx + v[i, j] * d_u_dy + g * d_eta_dx + g * Sf_x)
    v_new[i, j] = v[i, j] - dt * (u[i, j] * d_v_dx + v[i, j] * d_v_dy + g * d_eta_dy + g * Sf_y)

    return eta_new, u_new, v_new


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
    High-level driver to run the NLSWE simulation.

    Parameters
    ----------
    X, Y, Z : np.ndarray
        Mesh and bathymetry.
    eta0 : np.ndarray
        Initial free-surface elevation (from HHF engine).
    params : NLSWEParameters
    t_final : float
        Final simulation time (s).
    output_interval : float
        Interval at which to yield outputs (s).

    Yields
    ------
    t : float
        Current simulation time.
    eta, u, v : np.ndarray
        Current state.
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
