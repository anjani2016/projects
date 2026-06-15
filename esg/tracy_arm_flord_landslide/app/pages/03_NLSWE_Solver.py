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
    import plotly.graph_objects as go
except ModuleNotFoundError:
    st.error("Missing required package 'plotly'. Please install it using: pip install plotly")
    st.stop()

from src.geospatial.dem_loader import load_tracy_arm_dem
from src.geospatial.mesh_builder import build_structured_mesh
from src.engines.nlswe import NLSWEParameters, run_simulation

st.set_page_config(page_title="NLSWE Simulation", layout="wide")

st.title("📈 NLSWE Wave Propagation")
st.markdown("""
Simulate the propagation of the tsunami impulse wave through Tracy Arm Fjord using the **Nonlinear Shallow Water Equations (NLSWE)**.
The solver models wave velocity, bed shear friction, and boundary interactions as the wave travels down the channel.
""")

dem, x_dem, y_dem = load_tracy_arm_dem()
X, Y, Z = build_structured_mesh(dem, x_dem, y_dem)

if "eta0" not in st.session_state:
    st.warning("No η₀ found. Please generate it in the 'Impulse Wave Setup' page first.")
    st.stop()

eta0 = st.session_state["eta0"]

# Downsample the grids by stride 5 to ensure fast real-time solver execution (under 2 seconds)
stride = 5
X_sub = X[::stride, ::stride]
Y_sub = Y[::stride, ::stride]
Z_sub = Z[::stride, ::stride]
eta0_sub = eta0[::stride, ::stride]

st.subheader("Simulation Parameters")

# 1. Final simulation time
col_in, col_ctx = st.columns([3, 7])
with col_in:
    t_final = st.number_input("Final time (s)", 10.0, 2000.0, 150.0, step=10.0)
with col_ctx:
    st.markdown("<div style='padding-top: 25px;'><b>Total Simulation Time:</b> Duration of the tsunami wave propagation. A longer time allows the wave to travel further down the fjord channel.</div>", unsafe_allow_html=True)

# 2. Output interval
col_in, col_ctx = st.columns([3, 7])
with col_in:
    output_interval = st.number_input("Output interval (s)", 0.5, 50.0, 2.0, step=0.5)
with col_ctx:
    st.markdown("<div style='padding-top: 25px;'><b>Frame Interval:</b> Frequency of saving simulation frames. Smaller intervals produce smoother animations but require more memory.</div>", unsafe_allow_html=True)

# 3. Gravity
col_in, col_ctx = st.columns([3, 7])
with col_in:
    g = st.number_input("Gravity (m/s²)", 9.0, 10.0, 9.81, step=0.01)
with col_ctx:
    st.markdown("<div style='padding-top: 25px;'><b>Gravitational Acceleration ($g$):</b> Drives wave celerity. Wave propagation speed scales as $c = \\sqrt{g \\cdot h}$ where $h$ is the water depth.</div>", unsafe_allow_html=True)

# 4. Manning's n
col_in, col_ctx = st.columns([3, 7])
with col_in:
    manning_n = st.number_input("Manning n", 0.01, 0.1, 0.025, step=0.005, format="%.3f")
with col_ctx:
    st.markdown("<div style='padding-top: 25px;'><b>Bed Friction (Manning's $n$):</b> Roughness of the seabed. Higher friction drains wave energy, dampening peaks as it travels.</div>", unsafe_allow_html=True)

# 5. CFL number
col_in, col_ctx = st.columns([3, 7])
with col_in:
    cfl = st.number_input("CFL number", 0.05, 0.90, 0.15, step=0.05)
with col_ctx:
    st.markdown("<div style='padding-top: 25px;'><b>Courant-Friedrichs-Lewy Condition:</b> Governing stability criteria ($dt = \\text{CFL} \\cdot \\frac{dx}{c}$). Lower values ensure stable numerical integration through bends.</div>", unsafe_allow_html=True)

# 6. Minimum depth
col_in, col_ctx = st.columns([3, 7])
with col_in:
    min_depth = st.number_input("Minimum depth (m)", 0.01, 5.00, 1.00, step=0.10)
with col_ctx:
    st.markdown("<div style='padding-top: 25px;'><b>Wet-Dry Depth Threshold:</b> Depths below this limit are treated as dry land. Speeds up calculation along steep shoreline cliffs.</div>", unsafe_allow_html=True)

params = NLSWEParameters(g=g, manning_n=manning_n, cfl=cfl, min_depth=min_depth)

if st.button("Run Simulation"):
    st.info("Running NLSWE simulation… this may take a moment.")
    frames = []
    times = []

    for t, eta, u, v in run_simulation(X_sub, Y_sub, Z_sub, eta0_sub, params, t_final, output_interval):
        frames.append(eta)
        times.append(t)

    st.session_state["nlswe_frames"] = frames
    st.session_state["nlswe_times"] = times
    st.success(f"Simulation complete. Stored {len(frames)} frames.")

def build_propagation_plot(eta_frame, t):
    # Load the right-side-up structured mesh Z_sub
    if hasattr(Z_sub, "filled"):
        Z_sub_filled = Z_sub.filled(0.0)
    else:
        Z_sub_filled = np.asarray(Z_sub)
        
    # Crop the grids to match the scenario testing crop window (zoom-in)
    # This keeps layout alignment and excludes non-impacted areas
    i_sub_start, i_sub_end = 30, 115
    j_sub_start, j_sub_end = 40, 125
    
    geo_background_cropped = Z_sub_filled[j_sub_start:j_sub_end, i_sub_start:i_sub_end]
    wave_frame_cropped = eta_frame[j_sub_start:j_sub_end, i_sub_start:i_sub_end]
    
    # Calculate coordinate meters for the cropped grid
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
    # Mask out values close to 0.05 to reveal the background topography
    wave_frame_masked = np.where(np.abs(wave_frame_cropped) > 0.05, wave_frame_cropped, np.nan)
    
    if not np.all(np.isnan(wave_frame_masked)):
        zmax_val = float(max(5.0, np.nanmax(wave_frame_masked)))
        zmin_val = float(min(-2.0, np.nanmin(wave_frame_masked)))
        fig.add_trace(go.Heatmap(
            x=x_meters,
            y=y_meters,
            z=wave_frame_masked,
            colorscale='Viridis',
            zmin=zmin_val,
            zmax=zmax_val,
            zsmooth='best',
            colorbar=dict(
                title=dict(text="Wave Height η (m)", side="right")
            ),
            name="Tsunami Pulse"
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
            textfont=dict(size=11, color=marker["color"], family='Arial, sans-serif'),
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
        marker=dict(color='crimson', size=14, symbol='x', line=dict(width=2, color='white')),
        text=['<b>❌ Slide Impact Center</b>'],
        textposition='top center',
        textfont=dict(size=12, color='#b91c1c', family='Arial, sans-serif'),
        showlegend=False,
        name='Landslide Entry Site'
    ))

    fig.update_layout(
        title=f"Dynamic NLSWE Wave Propagation (Time: {t:.1f} s)",
        xaxis_title="UTM Zone 8N Easting Offset (Relative Meters)",
        yaxis_title="UTM Zone 8N Northing Offset (Relative Meters)",
        template="plotly_dark",
        xaxis=dict(range=[i_sub_start * 150.0, i_sub_end * 150.0], showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(range=[j_sub_start * 150.0, j_sub_end * 150.0], showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
        height=700
    )
    
    return fig


if "nlswe_frames" in st.session_state:
    st.subheader("Visualization")
    
    # Load the right-side-up structured mesh Z_sub
    if hasattr(Z_sub, "filled"):
        Z_sub_filled = Z_sub.filled(0.0)
    else:
        Z_sub_filled = np.asarray(Z_sub)
        
    # Crop the grids to match the scenario testing crop window (zoom-in)
    i_sub_start, i_sub_end = 30, 115
    j_sub_start, j_sub_end = 40, 125
    
    geo_background_cropped = Z_sub_filled[j_sub_start:j_sub_end, i_sub_start:i_sub_end]
    
    # Calculate coordinate meters for the cropped grid
    x_meters = (i_sub_start + np.arange(geo_background_cropped.shape[1])) * 5 * 30.0
    y_meters = (j_sub_start + np.arange(geo_background_cropped.shape[0])) * 5 * 30.0

    # Calculate dynamic color limits based on the initial wave (Frame 0) to prevent saturation
    first_frame = st.session_state["nlswe_frames"][0]
    first_frame_cropped = first_frame[j_sub_start:j_sub_end, i_sub_start:i_sub_end]
    zmax_val = float(max(5.0, np.max(first_frame_cropped)))
    zmin_val = float(min(-2.0, np.min(first_frame_cropped)))

    frames_count = len(st.session_state["nlswe_frames"])

    # 1. Build animation frames (updating only Trace 1: the wave heatmap)
    frames = []
    for idx in range(frames_count):
        raw_frame = st.session_state["nlswe_frames"][idx]
        wave_frame_cropped = raw_frame[j_sub_start:j_sub_end, i_sub_start:i_sub_end]
        wave_frame_masked = np.where(np.abs(wave_frame_cropped) > 0.05, wave_frame_cropped, np.nan)
        
        frames.append(go.Frame(
            data=[go.Heatmap(
                x=x_meters,
                y=y_meters,
                z=wave_frame_masked,
                colorscale='Viridis',
                zmin=zmin_val,
                zmax=zmax_val,
                zsmooth='best',
                showscale=True,
                colorbar=dict(
                    title=dict(text="Wave Height η (m)", side="right")
                )
            )],
            name=f"frame_{idx}",
            traces=[1]  # Modifies only the wave heatmap trace (second trace)
        ))

    # 2. Build the base figure (Frame 0 state)
    fig = go.Figure()

    # Trace 0: Fjord Topography
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

    # Trace 1: Wave Tsunami Pulse (Base)
    raw_frame_0 = st.session_state["nlswe_frames"][0]
    wave_frame_cropped_0 = raw_frame_0[j_sub_start:j_sub_end, i_sub_start:i_sub_end]
    wave_frame_masked_0 = np.where(np.abs(wave_frame_cropped_0) > 0.05, wave_frame_cropped_0, np.nan)
    
    fig.add_trace(go.Heatmap(
        x=x_meters,
        y=y_meters,
        z=wave_frame_masked_0,
        colorscale='Viridis',
        zmin=zmin_val,
        zmax=zmax_val,
        zsmooth='best',
        colorbar=dict(
            title=dict(text="Wave Height η (m)", side="right")
        ),
        name="Tsunami Pulse"
    ))

    # Trace 2-4: Real-World Geolocation Labels & Landmark Anchors
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
            textfont=dict(size=11, color=marker["color"], family='Arial, sans-serif'),
            showlegend=False,
            name=marker["text"].replace("<b>", "").replace("</b>", "")
        ))

    # Trace 5: Landslide Entry Site
    x0 = st.session_state.get("impact_x0", 454)
    y0 = st.session_state.get("impact_y0", 474)
    fig.add_trace(go.Scatter(
        x=[x0 * 30.0],
        y=[y0 * 30.0],
        mode='markers+text',
        marker=dict(color='crimson', size=14, symbol='x', line=dict(width=2, color='white')),
        text=['<b>❌ Slide Impact Center</b>'],
        textposition='top center',
        textfont=dict(size=12, color='#b91c1c', family='Arial, sans-serif'),
        showlegend=False,
        name='Landslide Entry Site'
    ))

    # 3. Configure native client-side Play/Pause controls and slider
    play_button = dict(
        label="▶ Play",
        method="animate",
        args=[None, {"frame": {"duration": 100, "redraw": True}, "fromcurrent": True, "transition": {"duration": 0}}]
    )
    pause_button = dict(
        label="⏸ Pause",
        method="animate",
        args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}}]
    )
    
    slider_steps = []
    for idx in range(frames_count):
        t_val = st.session_state["nlswe_times"][idx]
        step = dict(
            method="animate",
            args=[[f"frame_{idx}"], {"frame": {"duration": 100, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}],
            label=f"{t_val:.1f}s"
        )
        slider_steps.append(step)
        
    sliders = [dict(
        active=0,
        currentvalue={"prefix": "Simulation Time: ", "visible": True},
        pad={"t": 50},
        steps=slider_steps
    )]

    # 4. Apply layout configuration and assign frames
    fig.update_layout(
        title="Dynamic NLSWE Wave Propagation (Client-Side Playback)",
        xaxis_title="UTM Zone 8N Easting Offset (Relative Meters)",
        yaxis_title="UTM Zone 8N Northing Offset (Relative Meters)",
        template="plotly_dark",
        xaxis=dict(range=[i_sub_start * 150.0, i_sub_end * 150.0], showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(range=[j_sub_start * 150.0, j_sub_end * 150.0], showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
        height=750,
        updatemenus=[dict(
            type="buttons",
            direction="right",
            showactive=False,
            x=0.1,
            y=-0.12,
            xanchor="right",
            yanchor="top",
            pad={"t": 75, "r": 10},
            bgcolor='#1e293b',
            bordercolor='#3b82f6',
            borderwidth=1,
            font=dict(color='#ffffff', size=12, family='Arial'),
            buttons=[play_button, pause_button]
        )],
        sliders=sliders
    )

    fig.frames = frames

    st.plotly_chart(fig, use_container_width=True)
