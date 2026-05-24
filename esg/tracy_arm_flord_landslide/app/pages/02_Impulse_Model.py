import streamlit as st
import numpy as np
try:
    import plotly.express as px
except ModuleNotFoundError:
    st.error("Missing required package 'plotly'. Please install it using: pip install plotly")
    st.stop()

from src.geospatial.dem_loader import load_tracy_arm_dem
from src.geospatial.mesh_builder import build_structured_mesh
from src.engines.hhf import (
    SlideParameters,
    WaterColumnParameters,
    apply_eta0_to_mesh,
)

st.set_page_config(page_title="Impulse Wave Setup", layout="wide")

st.title("🌊 Impulse Wave Setup")
st.write("Configure the landslide and generate the initial impulse wave (η₀).")

# Load DEM and mesh
dem, x_dem, y_dem = load_tracy_arm_dem()
X, Y, Z = build_structured_mesh(dem, x_dem, y_dem)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Landslide Parameters")
    volume = st.number_input("Volume (m³)", 1e6, 5e9, 5e7, step=1e6, format="%.0f")
    mass = st.number_input("Mass (kg)", 1e9, 5e12, 1e10, step=1e9, format="%.0f")
    velocity = st.number_input("Impact velocity (m/s)", 5.0, 120.0, 40.0, step=1.0)
    thickness = st.number_input("Slide thickness (m)", 10.0, 500.0, 80.0, step=5.0)
    width = st.number_input("Slide width (m)", 50.0, 2000.0, 500.0, step=10.0)
    angle = st.number_input("Impact angle (deg)", 10.0, 80.0, 45.0, step=1.0)

with col2:
    st.subheader("Water Column & Impact Location")
    depth_at_impact = st.number_input("Water depth at impact (m)", 50.0, 1000.0, 300.0, step=10.0)
    x0 = st.slider("Impact X position (index)", 0, X.shape[1] - 1, X.shape[1] // 2)
    y0 = st.slider("Impact Y position (index)", 0, X.shape[0] - 1, X.shape[0] // 2)
    radius = st.number_input("Impact radius (m)", 50.0, 1000.0, 200.0, step=10.0)

slide = SlideParameters(
    volume=volume,
    mass=mass,
    impact_velocity=velocity,
    thickness=thickness,
    width=width,
    impact_angle_deg=angle,
)

water = WaterColumnParameters(depth_at_impact=depth_at_impact)

if st.button("Generate Initial Wave (η₀)"):
    impact_center = (X[0, x0], Y[y0, 0])
    eta0 = apply_eta0_to_mesh(X, Y, Z, impact_center, slide, water, radius=radius)

    st.subheader("Initial Free-Surface Elevation η₀ (m)")
    fig = px.imshow(
        eta0,
        origin="lower",
        color_continuous_scale="Turbo",
        labels={"color": "η₀ (m)"},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.session_state["eta0"] = eta0
    st.success("η₀ stored in session state for use in the NLSWE simulation page.")
