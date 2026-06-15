"""
dem_loader.py

Utilities for loading and preparing DEM (Digital Elevation Model) data
for the Tracy Arm Fjord landslide–tsunami Digital Twin.
"""

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.io import DatasetReader


def open_dem(dem_path: str | Path) -> DatasetReader:
    """
    Open a DEM GeoTIFF using rasterio.

    Parameters
    ----------
    dem_path : str | Path
        Path to the DEM file (e.g., data/raw/tracy_arm_dem.tif).

    Returns
    -------
    rasterio.io.DatasetReader
        Open raster dataset handle.

    Raises
    ------
    FileNotFoundError
        If the DEM file does not exist.
    """
    dem_path = Path(dem_path)
    if not dem_path.exists():
        raise FileNotFoundError(f"DEM file not found: {dem_path}")

    return rasterio.open(dem_path)


def load_dem_array(
    dem_path: str | Path,
    bounds: Optional[Tuple[float, float, float, float]] = None,
    masked: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load DEM as a NumPy array, optionally clipped to geographic bounds.

    Parameters
    ----------
    dem_path : str | Path
        Path to the DEM file.
    bounds : tuple[float, float, float, float], optional
        (minx, miny, maxx, maxy) in DEM CRS.
        If None, the full DEM is loaded.
    masked : bool, default True
        If True, returns a masked array where nodata values are masked.

    Returns
    -------
    dem : np.ndarray
        2D array of elevation values (masked if requested).
    x : np.ndarray
        1D array of x coordinates (eastings or longitude).
    y : np.ndarray
        1D array of y coordinates (northings or latitude, top-to-bottom).

    Notes
    -----
    - Coordinates are derived from the raster transform.
    - This function does not reproject; it assumes the DEM is already
      in the desired CRS for the simulation.
    """
    with open_dem(dem_path) as src:
        if bounds is not None:
            window = from_bounds(*bounds, transform=src.transform)
            dem = src.read(1, window=window, masked=masked)
            transform = src.window_transform(window)
        else:
            dem = src.read(1, masked=masked)
            transform = src.transform

        height, width = dem.shape

        # Build coordinate vectors from transform
        x_coords = np.arange(width) * transform.a + transform.c + transform.a / 2
        y_coords = np.arange(height) * transform.e + transform.f + transform.e / 2

        return dem, x_coords, y_coords


def load_tracy_arm_dem(
    base_dir: str | Path = "data/processed",
    filename: str = "tracy_arm_topobathy.tif",
    bounds: Optional[Tuple[float, float, float, float]] = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convenience wrapper for loading the Tracy Arm DEM from the standard path.

    Parameters
    ----------
    base_dir : str | Path, default "data/raw"
        Base directory where DEM is stored.
    filename : str, default "tracy_arm_dem.tif"
        DEM filename.
    bounds : tuple[float, float, float, float], optional
        Optional geographic bounds for clipping.

    Returns
    -------
    dem : np.ndarray
    x : np.ndarray
    y : np.ndarray
    """
    dem_path = Path(base_dir) / filename
    return load_dem_array(dem_path, bounds=bounds, masked=True)
