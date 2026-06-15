"""
# DEM & Bathymetry Explorer
This Streamlit page lets you:

    Load DEM + bathymetry

    Visualize them as heatmaps

    Inspect coordinate ranges

    Confirm alignment before simulation
"""


import streamlit as st
import numpy as np
import pandas as pd
import pydeck as pdk
from pyproj import Transformer
import plotly.graph_objects as go

import os
import sys
# Ensure project root is in sys.path so that 'src' imports work when deployed
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.geospatial.dem_loader import load_tracy_arm_dem
from src.geospatial.bathymetry_loader import load_tracy_arm_bathymetry
from src.geospatial.mesh_builder import build_structured_mesh


st.set_page_config(page_title="Data Explorer — Tracy Arm Twin", layout="wide")

st.title("🗺️ DEM & Bathymetry Explorer")
st.write("Inspect the fjord geometry before running simulations.")


# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------

st.header("Unified 3D Topobathymetric Map")

@st.cache_data
def get_cached_dem():
    dem, x_dem, y_dem = load_tracy_arm_dem()
    return build_structured_mesh(dem, x_dem, y_dem)

@st.cache_data
def get_cached_bathymetry():
    bath, x_bath, y_bath = load_tracy_arm_bathymetry()
    return build_structured_mesh(bath, x_bath, y_bath)

@st.cache_data
def load_and_downsample_data():
    # Load your real processed matrix
    matrix = np.load("data/processed/tracy_arm_mesh.npy")
    
    # Take every 5th pixel to guarantee fast UI loading times
    stride = 5
    return matrix[::stride, ::stride]

try:
    with st.spinner("Loading and converting coordinates... this may take a few seconds."):
        X_dem, Y_dem, Z_dem = get_cached_dem()
        X_bath, Y_bath, Z_bath = get_cached_bathymetry()
        z_data = load_and_downsample_data()
    
    # Create coordinate grids based on matrix shape
    x = np.arange(z_data.shape[1])
    y = np.arange(z_data.shape[0])
    
    # Construct a high-performance continuous 3D surface mesh
    fig = go.Figure(data=[go.Surface(
        z=z_data, 
        x=x, 
        y=y,
        colorscale='Earth',  # Beautiful natural rendering for land vs water
        cmin=-500,           # Caps the ocean depths color scale
        cmax=1500            # Caps the mountain peak color scale
    )])
    
    fig.update_layout(
        title="Unified 3D Topobathymetric Surface Mesh",
        scene=dict(
            xaxis_title="X Grid (Downsampled)",
            yaxis_title="Y Grid (Downsampled)",
            zaxis_title="Elevation / Depth (m)",
            aspectratio=dict(x=1, y=1, z=0.3) # Flattens vertical exaggeration to look realistic
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, use_container_width=True)

except FileNotFoundError:
    st.error("Processed mesh file missing. Run data_processor.py first.")


# ---------------------------------------------------------
# Metadata
# ---------------------------------------------------------

st.header("Metadata")
st.write(f"DEM shape: {Z_dem.shape}")
st.write(f"Bathymetry shape: {Z_bath.shape}")

st.write("Coordinate ranges:")
st.write(f"X: {X_dem.min():.2f} → {X_dem.max():.2f}")
st.write(f"Y: {Y_dem.min():.2f} → {Y_dem.max():.2f}")
