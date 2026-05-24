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
st.info("Loading and converting coordinates... this may take a few seconds.")

@st.cache_data
def get_cached_dem():
    dem, x_dem, y_dem = load_tracy_arm_dem()
    return build_structured_mesh(dem, x_dem, y_dem)

@st.cache_data
def get_cached_bathymetry():
    bath, x_bath, y_bath = load_tracy_arm_bathymetry()
    return build_structured_mesh(bath, x_bath, y_bath)

X_dem, Y_dem, Z_dem = get_cached_dem()
X_bath, Y_bath, Z_bath = get_cached_bathymetry()

# Helper function to downsample and convert to pydeck DataFrame
@st.cache_data
def prepare_3d_data(_X, _Y, _Z, is_bathy=False, step=15):
    X_sub = _X[::step, ::step].flatten()
    Y_sub = _Y[::step, ::step].flatten()
    Z_sub = _Z[::step, ::step].flatten()
    
    # Filter NoData / Zeros
    if is_bathy:
        mask = Z_sub < 0
    else:
        mask = Z_sub > 0
        
    X_sub = X_sub[mask]
    Y_sub = Y_sub[mask]
    Z_sub = Z_sub[mask]
    
    # Convert UTM to WGS84
    transformer = Transformer.from_crs("epsg:26908", "epsg:4326", always_xy=True)
    lon, lat = transformer.transform(X_sub, Y_sub)
    
    df = pd.DataFrame({'lon': lon, 'lat': lat, 'elevation': Z_sub})
    
    # Color mapping
    if len(df) > 0:
        z_min, z_max = df['elevation'].min(), df['elevation'].max()
        norm = (df['elevation'] - z_min) / (z_max - z_min + 1e-5)
        if is_bathy:
            # Deep blue to light blue
            df['r'] = 0
            df['g'] = (100 + 100 * norm).astype(int)
            df['b'] = (150 + 105 * norm).astype(int)
        else:
            # Green to white for mountains
            df['r'] = (50 + 205 * norm).astype(int)
            df['g'] = (150 + 105 * norm).astype(int)
            df['b'] = (50 + 205 * norm).astype(int)
            
    return df

df_dem = prepare_3d_data(X_dem, Y_dem, Z_dem, is_bathy=False, step=15)
df_bath = prepare_3d_data(X_bath, Y_bath, Z_bath, is_bathy=True, step=15)

dem_layer = pdk.Layer(
    "PointCloudLayer",
    data=df_dem,
    get_position=["lon", "lat", "elevation"],
    get_color=["r", "g", "b", 255],
    point_size=5,
    pickable=True,
)

bathy_layer = pdk.Layer(
    "PointCloudLayer",
    data=df_bath,
    get_position=["lon", "lat", "elevation"],
    get_color=["r", "g", "b", 255],
    point_size=5,
    pickable=True,
)

# Set initial view state centered on the fjord
view_state = pdk.ViewState(
    latitude=df_dem['lat'].mean(),
    longitude=df_dem['lon'].mean(),
    zoom=10,
    pitch=50,
    bearing=0
)

deck = pdk.Deck(
    layers=[dem_layer, bathy_layer],
    initial_view_state=view_state,
    map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    tooltip={"text": "Elevation: {elevation} m"}
)

st.pydeck_chart(deck, use_container_width=True)


# ---------------------------------------------------------
# Metadata
# ---------------------------------------------------------

st.header("Metadata")
st.write(f"DEM shape: {Z_dem.shape}")
st.write(f"Bathymetry shape: {Z_bath.shape}")

st.write("Coordinate ranges:")
st.write(f"X: {x_dem.min():.2f} → {x_dem.max():.2f}")
st.write(f"Y: {y_dem.min():.2f} → {y_dem.max():.2f}")
