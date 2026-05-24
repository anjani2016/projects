"""
hhf.py (version1)

Heller–Hager–Fritz (HHF) impulse product parameter engine
for landslide-generated impulse waves.

Consumes:
- Structured mesh (X, Y, Z)
- Slide parameters
- Water column parameters

Produces:
- η0(x, y): initial free-surface elevation field
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import numpy as np


# ---------------------------------------------------------
# Parameter Data Classes
# ---------------------------------------------------------

@dataclass
class SlideParameters:
    volume: float              # m^3
    mass: float                # kg
    impact_velocity: float     # m/s
    thickness: float           # m
    width: float               # m
    impact_angle_deg: float    # degrees


@dataclass
class WaterColumnParameters:
    depth_at_impact: float     # m
    density: float = 1000.0    # kg/m^3
    g: float = 9.81            # m/s^2


# ---------------------------------------------------------
# Core HHF Physics
# ---------------------------------------------------------

def compute_impulse_parameter(slide: SlideParameters, water: WaterColumnParameters) -> float:
    """Compute the HHF non-dimensional impulse parameter P."""
    h0 = water.depth_at_impact
    vs = slide.impact_velocity
    ss = slide.thickness
    ms = slide.mass
    b = slide.width
    rho_w = water.density
    g = water.g

    F = vs / np.sqrt(g * h0)          # Froude number
    S = ss / h0                       # Relative slide thickness
    M = (rho_w * b * h0**2) / ms      # Relative slide mass
    alpha = np.deg2rad(slide.impact_angle_deg)

    P = F * np.sqrt(S) * M**0.25 * np.sqrt(np.cos(2 * alpha / 3))
    return P


def compute_initial_wave_amplitude(slide: SlideParameters, water: WaterColumnParameters) -> float:
    """Compute η0 at the impact zone."""
    P = compute_impulse_parameter(slide, water)
    return 0.25 * water.depth_at_impact * P**(4/5)


# ---------------------------------------------------------
# Mapping η0 onto the Mesh
# ---------------------------------------------------------

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
    Create a spatial η0(x, y) field using a Gaussian-like decay
    from the impact center.
    """
    x0, y0 = impact_center
    eta0_max = compute_initial_wave_amplitude(slide, water)

    r = np.sqrt((X - x0)**2 + (Y - y0)**2)
    eta0_field = eta0_max * np.exp(-(r**2) / (2 * radius**2))

    # Mask out land (Z > 0)
    eta0_field = np.where(Z < 0, eta0_field, 0.0)

    return eta0_field
