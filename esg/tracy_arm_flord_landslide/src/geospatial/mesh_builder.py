"""
mesh_builder.py

Builds structured 2D/3D meshes from DEM or bathymetry data
for the Tracy Arm Fjord landslide–tsunami Digital Twin.

This module converts raster-based elevation/depth data into:
- Simulation-ready 2D grids (X, Y, Z)
- Optional PyVista meshes for 3D visualization
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

try:
    import pyvista as pv
    _HAS_PYVISTA = True
except ImportError:
    _HAS_PYVISTA = False


# ---------------------------------------------------------
# Core Mesh Builder
# ---------------------------------------------------------

def build_structured_mesh(
    dem: np.ndarray,
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    flip_y: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build a structured 2D meshgrid from DEM arrays.

    Parameters
    ----------
    dem : np.ndarray
        2D elevation or depth array.
    x_coords : np.ndarray
        1D array of x coordinates.
    y_coords : np.ndarray
        1D array of y coordinates.
    flip_y : bool, default True
        DEM rasters typically have origin at top-left.
        For simulation, we flip Y so origin is bottom-left.

    Returns
    -------
    X : np.ndarray
        2D meshgrid of x coordinates.
    Y : np.ndarray
        2D meshgrid of y coordinates.
    Z : np.ndarray
        2D array of elevations/depths aligned with X, Y.
    """
    if flip_y:
        dem = np.flipud(dem)
        y_coords = y_coords[::-1]

    X, Y = np.meshgrid(x_coords, y_coords)

    return X, Y, dem


# ---------------------------------------------------------
# PyVista Mesh Builder (Optional)
# ---------------------------------------------------------

def build_pyvista_mesh(
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
    name: str = "fjord_mesh"
):
    """
    Convert structured mesh into a PyVista surface mesh.

    Parameters
    ----------
    X, Y, Z : np.ndarray
        Structured mesh arrays.
    name : str
        Name of the mesh object.

    Returns
    -------
    pv.PolyData
        PyVista mesh for 3D visualization.

    Raises
    ------
    ImportError
        If PyVista is not installed.
    """
    if not _HAS_PYVISTA:
        raise ImportError("PyVista is required for 3D mesh visualization.")

    # Stack into (N, 3) point cloud
    points = np.column_stack((X.ravel(), Y.ravel(), Z.ravel()))

    # Build structured grid
    ny, nx = Z.shape
    grid = pv.StructuredGrid()
    grid.points = points
    grid.dimensions = (nx, ny, 1)
    grid["elevation"] = Z.ravel(order="C")

    grid.name = name
    return grid


# ---------------------------------------------------------
# Convenience Wrapper
# ---------------------------------------------------------

def build_fjord_mesh(
    dem: np.ndarray,
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    return_pyvista: bool = False
):
    """
    High-level wrapper to build simulation mesh and optional PyVista mesh.

    Parameters
    ----------
    dem : np.ndarray
        DEM elevation/depth array.
    x_coords : np.ndarray
        X coordinate vector.
    y_coords : np.ndarray
        Y coordinate vector.
    return_pyvista : bool, default False
        If True, returns a PyVista mesh as well.

    Returns
    -------
    X, Y, Z : np.ndarray
        Structured simulation mesh.
    pv_mesh : pv.StructuredGrid (optional)
        PyVista mesh for visualization.
    """
    X, Y, Z = build_structured_mesh(dem, x_coords, y_coords)

    if return_pyvista:
        pv_mesh = build_pyvista_mesh(X, Y, Z)
        return X, Y, Z, pv_mesh

    return X, Y, Z
