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

dem, x_dem, y_dem = load_tracy_arm_dem()
X, Y, Z = build_structured_mesh(dem, x_dem, y_dem)

if "nlswe_frames" not in st.session_state:
    st.warning("No NLSWE simulation found. Please run it in the 'NLSWE Simulation' page first.")
    st.stop()

frames = st.session_state["nlswe_frames"]
times = st.session_state["nlswe_times"]

st.subheader("Select Wall Cross-Section")
orientation = st.radio("Orientation", ["Vertical slice (constant X)", "Horizontal slice (constant Y)"])

if orientation == "Vertical slice (constant X)":
    x_idx = st.slider("X index", 0, X.shape[1] - 1, X.shape[1] // 2)
    x_line = X[:, x_idx]
    z_line = Z[:, x_idx]
    eta_max_along_line = np.max(np.stack(frames), axis=0)[:, x_idx]
    coord_label = "Y coordinate"
    coord_vals = Y[:, 0]
else:
    y_idx = st.slider("Y index", 0, Y.shape[0] - 1, Y.shape[0] // 2)
    x_line = X[y_idx, :]
    z_line = Z[y_idx, :]
    eta_max_along_line = np.max(np.stack(frames), axis=0)[y_idx, :]
    coord_label = "X coordinate"
    coord_vals = X[0, :]

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
