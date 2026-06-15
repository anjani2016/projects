"""
bathymetry_loader.py

Loads NOAA/GEBCO bathymetry grids for Tracy Arm Fjord.
Produces depth arrays aligned with DEM conventions.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import rasterio
from rasterio.windows import from_bounds


def open_bathymetry(path: str | Path):
    """Open bathymetry GeoTIFF."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Bathymetry file not found: {path}")
    return rasterio.open(path)


def load_bathymetry_array(
    path: str | Path,
    bounds: Optional[Tuple[float, float, float, float]] = None,
    masked: bool = True
):
    """
    Load bathymetry as NumPy array, optionally clipped to bounds.
    Depth values are negative (below sea level).
    """
    with open_bathymetry(path) as src:
        if bounds:
            window = from_bounds(*bounds, transform=src.transform)
            depth = src.read(1, window=window, masked=masked)
            transform = src.window_transform(window)
        else:
            depth = src.read(1, masked=masked)
            transform = src.transform

        # Ensure depths are negative representing subsurface bathymetry
        if np.min(depth) >= 0 and np.max(depth) > 0:
            depth = -np.abs(depth)

        h, w = depth.shape

        x = np.arange(w) * transform.a + transform.c + transform.a / 2
        y = np.arange(h) * transform.e + transform.f + transform.e / 2

        return depth, x, y


def load_tracy_arm_bathymetry(
    base_dir: Optional[str | Path] = None,
    filename: str = "tracy_arm_bathymetry_clipped.tif",
    bounds: Optional[Tuple[float, float, float, float]] = None
):
    """Convenience wrapper for standard bathymetry path."""
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent / "data/processed"
    path = Path(base_dir) / filename
    return load_bathymetry_array(path, bounds=bounds)
