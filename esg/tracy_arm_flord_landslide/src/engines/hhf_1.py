"""
hhf.py

Heller–Hager–Fritz (HHF) impulse product parameter engine
for landslide-generated impulse waves.

This module computes the initial free-surface elevation field (η0)
given landslide and water-column parameters, using the mesh (X, Y, Z).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass
class SlideParameters:
    """
    Parameters describing the landslide impacting the water.
    """
    volume: float          # m^3
    mass: float            # kg
    impact_velocity: float # m/s
    thickness: float       # m (characteristic slide thickness)
    width: float           # m (slide width along shoreline)
    impact_angle_deg: float  # degrees


@dataclass
class WaterColumnParameters:
    """
    Parameters describing the water column at the impact zone.
    """
    depth_at_impact: float  # m (h0)
    density: float = 1000.0 # kg/m^3
    g: float = 9.81         # m/s^2


def compute_impulse_parameter(
    slide: SlideParameters,
    water: WaterColumnParameters
) -> float:
    """
    Compute the non-dimensional impulse parameter P
    following the Heller–Hager–Fritz framework (simplified).

    Returns
    -------
    P : float
        Non-dimensional impulse parameter.
    """
    h0 = water.depth_at_impact
    vs = slide.impact_velocity
    ss = slide.thickness
    ms = slide.mass
    b = slide.width
    rho_w = water.density
    g = water.g

    # Froude number
    F = vs / np.sqrt(g * h0)

    # Relative slide thickness
    S = ss / h0

    # Relative slide mass
    M = (rho_w * b * h0**2) / ms

    alpha = np.deg2rad(slide.impact_angle_deg)

    P = F * np.sqrt(S) * M**0.25 * np.sqrt(np.cos(2 * alpha / 3.0))
    return P


def compute_initial_wave_amplitude(
    slide: SlideParameters,
    water: WaterColumnParameters
) -> float:
    """
    Compute the initial maximum wave amplitude η0 at the impact zone.

    Returns
    -------
    eta0 : float
        Initial wave amplitude (m).
    """
    P = compute_impulse_parameter(slide, water)
    h0 = water.depth_at_impact
    eta0 = 0.25 * h0 * P**(4.0 / 5.0)
    return eta0


def apply_eta0_to_mesh(
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
    impact_center: Tuple[float, float],
    slide: SlideParameters,
    water: WaterColumnParameters,
    radius: float = 200.0
) -> np.ndarray:
    """
    Map the initial wave amplitude η0 onto the mesh as a localized
    Gaussian-like bump around the impact center.

    Parameters
    ----------
    X, Y, Z : np.ndarray
        Mesh coordinates and bathymetry/elevation.
    impact_center : (float, float)
        (x0, y0) coordinates of the slide impact point.
    slide : SlideParameters
    water : WaterColumnParameters
    radius : float, default 200.0
        Characteristic radius of influence (m).

    Returns
    -------
    eta0_field : np.ndarray
        2D array of initial free-surface elevation η0(x, y).
    """
    x0, y0 = impact_center
    eta0_max = compute_initial_wave_amplitude(slide, water)

    # Distance from impact center
    r = np.sqrt((X - x0)**2 + (Y - y0)**2)

    # Simple radial decay (Gaussian-like)
    eta0_field = eta0_max * np.exp(-(r**2) / (2 * radius**2))

    # Optionally, you could mask out land (Z > 0) if DEM includes land
    eta0_field = np.where(Z < 0, eta0_field, 0.0)

    return eta0_field
