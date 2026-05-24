import streamlit as st
import numpy as np
try:
    import plotly.express as px
except ModuleNotFoundError:
    st.error("Missing required package 'plotly'. Please install it using: pip install plotly")
    st.stop()

st.set_page_config(page_title="Model Comparison", layout="wide")

st.title("📊 Model Comparison Dashboard")
st.write("Compare empirical (HHF) vs NLSWE vs observed run-up / wave heights.")

if "eta0" not in st.session_state:
    st.warning("No HHF initial wave (η₀) found. Generate it in 'Impulse Wave Setup'.")
    st.stop()

if "nlswe_frames" not in st.session_state:
    st.warning("No NLSWE simulation found. Run it in 'NLSWE Simulation'.")
    st.stop()

eta0 = st.session_state["eta0"]
frames = st.session_state["nlswe_frames"]
times = st.session_state["nlswe_times"]

st.subheader("Global Metrics")

hhf_max = np.max(eta0)
nlswe_max = np.max(np.stack(frames))
st.write(f"**HHF η₀ max:** {hhf_max:.2f} m")
st.write(f"**NLSWE η max:** {nlswe_max:.2f} m")
st.write("**Observed run-up:** ~481 m (field data, not directly comparable to η but used as a reference).")

st.subheader("Spatial Comparison Snapshot")
idx = st.slider("Select NLSWE frame for comparison", 0, len(frames) - 1, 0)
eta_frame = frames[idx]
t = times[idx]

col1, col2 = st.columns(2)

with col1:
    st.write("HHF Initial Wave (η₀)")
    fig_hhf = px.imshow(
        eta0,
        origin="lower",
        color_continuous_scale="Turbo",
        labels={"color": "η₀ (m)"},
    )
    st.plotly_chart(fig_hhf, use_container_width=True)

with col2:
    st.write(f"NLSWE Wave at t = {t:.1f} s")
    fig_nlswe = px.imshow(
        eta_frame,
        origin="lower",
        color_continuous_scale="Turbo",
        labels={"color": "η (m)"},
    )
    st.plotly_chart(fig_nlswe, use_container_width=True)

st.subheader("Residuals (NLSWE - HHF)")
residuals = eta_frame - eta0
fig_res = px.imshow(
    residuals,
    origin="lower",
    color_continuous_scale="RdBu",
    labels={"color": "Δη (m)"},
)
st.plotly_chart(fig_res, use_container_width=True)
