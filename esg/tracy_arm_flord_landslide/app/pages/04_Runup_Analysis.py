import os
import sys
# Ensure project root is in sys.path so that 'src' imports work when deployed
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit as st
import numpy as np
try:
    import plotly.express as px
except ModuleNotFoundError:
    st.error("Missing required package 'plotly'. Please install it using: pip install plotly")
    st.stop()

from src.geospatial.dem_loader import load_tracy_arm_dem
from src.geospatial.mesh_builder import build_structured_mesh

st.set_page_config(page_title="Run-Up Analysis", layout="wide")

st.title("⛰️ Run-Up Analysis")
st.write("Estimate maximum run-up along a selected fjord wall and compare with the observed 481 m.")

with st.expander("📖 What is Tsunami Run-Up? (Scientific Diagram)"):
    st.image("app/tsunami_runup_explanation.png", caption="Cross-section schematic of tsunami run-up on a steep rocky fjord wall.")
    st.markdown("""
    **Run-up** is the maximum vertical height the tsunami wave reaches on land above the normal sea level. 
    As the incoming wave approaches a steep shore, its horizontal velocity is blocked by the rocky wall, converting its kinetic energy into a vertical surge up the cliff face.
    """)

dem, x_dem, y_dem = load_tracy_arm_dem()
X, Y, Z = build_structured_mesh(dem, x_dem, y_dem)

# Downsample the grids by stride 5 to match the NLSWE solver resolution
stride = 5
X_sub = X[::stride, ::stride]
Y_sub = Y[::stride, ::stride]
Z_sub = Z[::stride, ::stride]

if "nlswe_frames" not in st.session_state:
    st.warning("No NLSWE simulation found. Please run it in the 'NLSWE Simulation' page first.")
    st.stop()

frames = st.session_state["nlswe_frames"]
times = st.session_state["nlswe_times"]

st.subheader("Select Wall Cross-Section")
orientation = st.radio("Orientation", ["Vertical slice (constant X)", "Horizontal slice (constant Y)"])

if orientation == "Vertical slice (constant X)":
    x_idx = st.slider("Select slice profile X-index", 0, X_sub.shape[1] - 1, X_sub.shape[1] // 2)
    x_pos_m = X_sub[0, x_idx]
    st.info(f"📍 Slicing vertically at Easting: {x_pos_m:,.1f} m (UTM Zone 8N Coordinate)")
    x_line = X_sub[:, x_idx]
    z_line = Z_sub[:, x_idx]
    eta_max_along_line = np.max(np.stack(frames), axis=0)[:, x_idx]
    coord_label = "UTM Zone 8N Northing (m)"
    coord_vals = Y_sub[:, 0]
else:
    y_idx = st.slider("Select slice profile Y-index", 0, Y_sub.shape[0] - 1, Y_sub.shape[0] // 2)
    y_pos_m = Y_sub[y_idx, 0]
    st.info(f"📍 Slicing horizontally at Northing: {y_pos_m:,.1f} m (UTM Zone 8N Coordinate)")
    x_line = X_sub[y_idx, :]
    z_line = Z_sub[y_idx, :]
    eta_max_along_line = np.max(np.stack(frames), axis=0)[y_idx, :]
    coord_label = "UTM Zone 8N Easting (m)"
    coord_vals = X_sub[0, :]

st.subheader("Maximum Free-Surface Elevation Along Section")
runup_height = eta_max_along_line - z_line  # crude proxy

fig = px.line(
    x=coord_vals,
    y=runup_height,
    labels={"x": coord_label, "y": "Water elevation above bed (m)"},
)
st.plotly_chart(fig, use_container_width=True)

st.info("Observed maximum run-up: ~481 m (field measurement).")
st.write(f"Simulated maximum along this section: {runup_height.max():.1f} m")
