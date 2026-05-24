import streamlit as st
import numpy as np
try:
    import plotly.express as px
except ModuleNotFoundError:
    st.error("Missing required package 'plotly'. Please install it using: pip install plotly")
    st.stop()

from src.geospatial.dem_loader import load_tracy_arm_dem
from src.geospatial.mesh_builder import build_structured_mesh
from src.engines.nlswe import NLSWEParameters, run_simulation

st.set_page_config(page_title="NLSWE Simulation", layout="wide")

st.title("📈 NLSWE Wave Propagation")
st.write("Simulate the propagation of the impulse wave through the fjord.")

dem, x_dem, y_dem = load_tracy_arm_dem()
X, Y, Z = build_structured_mesh(dem, x_dem, y_dem)

if "eta0" not in st.session_state:
    st.warning("No η₀ found. Please generate it in the 'Impulse Wave Setup' page first.")
    st.stop()

eta0 = st.session_state["eta0"]

st.subheader("Simulation Parameters")
col1, col2 = st.columns(2)

with col1:
    t_final = st.number_input("Final time (s)", 10.0, 2000.0, 600.0, step=10.0)
    output_interval = st.number_input("Output interval (s)", 1.0, 200.0, 30.0, step=1.0)

with col2:
    g = st.number_input("Gravity (m/s²)", 9.0, 10.0, 9.81, step=0.01)
    manning_n = st.number_input("Manning n", 0.01, 0.1, 0.025, step=0.005, format="%.3f")
    cfl = st.number_input("CFL number", 0.1, 0.9, 0.4, step=0.05)
    min_depth = st.number_input("Minimum depth (m)", 0.01, 1.0, 0.1, step=0.01)

params = NLSWEParameters(g=g, manning_n=manning_n, cfl=cfl, min_depth=min_depth)

if st.button("Run Simulation"):
    st.info("Running NLSWE simulation… this may take a moment.")
    frames = []
    times = []

    for t, eta, u, v in run_simulation(X, Y, Z, eta0, params, t_final, output_interval):
        frames.append(eta)
        times.append(t)

    st.session_state["nlswe_frames"] = frames
    st.session_state["nlswe_times"] = times
    st.success(f"Simulation complete. Stored {len(frames)} frames.")

if "nlswe_frames" in st.session_state:
    st.subheader("Visualization")
    idx = st.slider(
        "Select time frame",
        0,
        len(st.session_state["nlswe_frames"]) - 1,
        0,
    )
    eta_frame = st.session_state["nlswe_frames"][idx]
    t = st.session_state["nlswe_times"][idx]

    st.write(f"Time: {t:.1f} s")
    fig = px.imshow(
        eta_frame,
        origin="lower",
        color_continuous_scale="Turbo",
        labels={"color": "η (m)"},
    )
    st.plotly_chart(fig, use_container_width=True)
