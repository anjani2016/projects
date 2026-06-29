import os
import sys
# Ensure project root is in sys.path so that 'src' imports work when deployed
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit as st
import numpy as np
try:
    import plotly.graph_objects as go
except ModuleNotFoundError:
    st.error("Missing required package 'plotly'. Please install it using: pip install plotly")
    st.stop()

from src.geospatial.dem_loader import load_tracy_arm_dem
from src.geospatial.mesh_builder import build_structured_mesh

st.set_page_config(page_title="Model Comparison", layout="wide")

st.title("📊 Model Comparison Dashboard")
st.write("Compare empirical (HHF) vs NLSWE vs observed run-up / wave heights.")

if "eta0" not in st.session_state:
    st.warning("No HHF initial wave (η₀) found. Generate it in 'Impulse Wave Setup'.")
    st.stop()

if "nlswe_frames" not in st.session_state:
    st.warning("No NLSWE simulation found. Run it in 'NLSWE Simulation'.")
    st.stop()

# Load DEM to build the mesh for the topography background
dem, x_dem, y_dem = load_tracy_arm_dem()
X, Y, Z = build_structured_mesh(dem, x_dem, y_dem)

# Stride is 5 to match the solver frames resolution
stride = 5
Z_sub = Z[::stride, ::stride]

eta0 = st.session_state["eta0"]
eta0_sub = eta0[::stride, ::stride]
frames = st.session_state["nlswe_frames"]
times = st.session_state["nlswe_times"]

st.subheader("Global Metrics")

hhf_max = np.max(eta0)
nlswe_max = np.max(np.stack(frames))
st.write(f"**HHF η₀ max:** {hhf_max:.2f} m")
st.write(f"**NLSWE η max:** {nlswe_max:.2f} m")
st.write("**Observed run-up:** ~481 m (field data, not directly comparable to η but used as a reference).")

# Calculate dynamic color limits based on the initial wave (Frame 0) to align scales
first_frame = frames[0]
i_sub_start, i_sub_end = 30, 115
j_sub_start, j_sub_end = 40, 125
first_frame_cropped = first_frame[j_sub_start:j_sub_end, i_sub_start:i_sub_end]

zmax_val = float(max(5.0, np.max(first_frame_cropped)))
zmin_val = float(min(-2.0, np.min(first_frame_cropped)))

def build_comparison_plot(eta_data, title, colorscale, zmin, zmax, label, showscale=True):
    if hasattr(Z_sub, "filled"):
        Z_sub_filled = Z_sub.filled(0.0)
    else:
        Z_sub_filled = np.asarray(Z_sub)
        
    geo_background_cropped = Z_sub_filled[j_sub_start:j_sub_end, i_sub_start:i_sub_end]
    wave_frame_cropped = eta_data[j_sub_start:j_sub_end, i_sub_start:i_sub_end]
    
    x_meters = (i_sub_start + np.arange(geo_background_cropped.shape[1])) * 5 * 30.0
    y_meters = (j_sub_start + np.arange(geo_background_cropped.shape[0])) * 5 * 30.0

    fig = go.Figure()

    # Layer A: Plot the true fjord geometry as a grayscale/muted heatmap
    fig.add_trace(go.Heatmap(
        x=x_meters,
        y=y_meters,
        z=geo_background_cropped,
        colorscale='Greys',
        showscale=False,
        opacity=0.25,
        zsmooth='best',
        hoverinfo='skip',
        name="Fjord Topography"
    ))

    # Layer B: Overlay the dynamic wave height frame
    wave_frame_masked = np.where(np.abs(wave_frame_cropped) > 0.05, wave_frame_cropped, np.nan)
    
    if not np.all(np.isnan(wave_frame_masked)):
        fig.add_trace(go.Heatmap(
            x=x_meters,
            y=y_meters,
            z=wave_frame_masked,
            colorscale=colorscale,
            zmin=zmin,
            zmax=zmax,
            zsmooth='best',
            showscale=showscale,
            colorbar=dict(
                title=dict(text=label, side="right")
            ),
            name="Wave Amplitude"
        ))

    # Layer C: Real-World Geolocation Labels & Landmark Anchors
    landmarks = [
        {"x": 13620, "y": 14220, "text": "<b>📍 South Sawyer Glacier (Origin)</b>", "color": "#b91c1c", "position": "bottom center"},
        {"x": 10200, "y": 11000, "text": "<b>🛳️ Cruise Ship Transit Lane</b>", "color": "#1d4ed8", "position": "top center"},
        {"x": 12000, "y": 12800, "text": "<b>🌊 Tracy Arm Fjord</b>", "color": "#0f766e", "position": "middle center"}
    ]
    
    for marker in landmarks:
        is_fjord = "Tracy Arm Fjord" in marker["text"]
        mode = "text" if is_fjord else "markers+text"
        fig.add_trace(go.Scatter(
            x=[marker["x"]],
            y=[marker["y"]],
            mode=mode,
            text=[marker["text"]],
            textposition=marker["position"],
            marker=dict(color=marker["color"], size=8, symbol='circle') if not is_fjord else None,
            textfont=dict(size=10, color=marker["color"], family='Arial, sans-serif'),
            showlegend=False,
            name=marker["text"].replace("<b>", "").replace("</b>", "")
        ))

    # Mark the current impact location (snapped to water edge)
    x0 = st.session_state.get("impact_x0", 454)
    y0 = st.session_state.get("impact_y0", 474)
    fig.add_trace(go.Scatter(
        x=[x0 * 30.0],
        y=[y0 * 30.0],
        mode='markers+text',
        marker=dict(color='crimson', size=12, symbol='x', line=dict(width=2, color='white')),
        text=['<b>❌ Slide Impact Center</b>'],
        textposition='top center',
        textfont=dict(size=11, color='#b91c1c', family='Arial, sans-serif'),
        showlegend=False,
        name='Landslide Entry Site'
    ))

    fig.update_layout(
        title=title,
        xaxis_title="UTM Zone 8N Easting Offset (Relative Meters)",
        yaxis_title="UTM Zone 8N Northing Offset (Relative Meters)",
        template="plotly_dark",
        xaxis=dict(range=[i_sub_start * 150.0, i_sub_end * 150.0], showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(range=[j_sub_start * 150.0, j_sub_end * 150.0], showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
        height=500
    )
    return fig

st.subheader("Spatial Comparison Snapshot")
idx = st.slider("Select NLSWE frame for comparison", 0, len(frames) - 1, 0)
eta_frame = frames[idx]
t = times[idx]

col1, col2 = st.columns(2)

with col1:
    fig_hhf = build_comparison_plot(
        eta0_sub,
        "HHF Initial Wave (η₀) - Geographically Aligned",
        "Viridis",
        zmin_val,
        zmax_val,
        "η₀ (m)"
    )
    st.plotly_chart(fig_hhf, use_container_width=True)

with col2:
    fig_nlswe = build_comparison_plot(
        eta_frame,
        f"NLSWE Wave at t = {t:.1f} s - Geographically Aligned",
        "Viridis",
        zmin_val,
        zmax_val,
        "η (m)"
    )
    st.plotly_chart(fig_nlswe, use_container_width=True)

st.subheader("Residuals (NLSWE - HHF)")
residuals = eta_frame - eta0_sub
# Residuals are plotted symmetrically around 0 with diverging RdBu scale
res_lim = max(abs(zmin_val), zmax_val)
fig_res = build_comparison_plot(
    residuals,
    "Spatial Residual Difference Map (NLSWE - HHF)",
    "RdBu",
    -res_lim,
    res_lim,
    "Δη (m)"
)
st.plotly_chart(fig_res, use_container_width=True)
