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
from src.engines.hhf import (
    SlideParameters,
    WaterColumnParameters,
    apply_eta0_to_mesh,
    compute_initial_wave_amplitude,
)

st.set_page_config(page_title="Scenario Testing & Climate Risk Stress-Testing", layout="wide")

st.title("🌊 Scenario Testing & Climate Risk Stress-Testing")
st.write("Configure landslide scenario baselines, evaluate impulse waves under climate-risk assumptions, and stress-test the fjord environment.")

dem, x_dem, y_dem = load_tracy_arm_dem()
X, Y, Z = build_structured_mesh(dem, x_dem, y_dem)

# Define preset defaults
PRESETS = {
    "2025 Observed Tracy Arm Event (Baseline)": {
        "vol": 5.5e7, "mass": 1.1e11, "vel": 40.0, "thick": 75.0, "width": 500.0, "angle": 42.0, "depth": 300.0, "radius": 500.0
    },
    "Maximum Credible Failure (Worst-Case)": {
        "vol": 1.2e8, "mass": 2.4e11, "vel": 60.0, "thick": 110.0, "width": 800.0, "angle": 50.0, "depth": 400.0, "radius": 800.0
    },
    "Minor Localized Slope Detachment": {
        "vol": 5.0e6, "mass": 1.0e10, "vel": 25.0, "thick": 20.0, "width": 200.0, "angle": 30.0, "depth": 150.0, "radius": 150.0
    }
}

col1, col2 = st.columns(2)

with col1:
    st.subheader("Select Scenario Baseline")
    scenario_preset = st.selectbox(
        "Choose a pre-configured risk scenario:",
        ["Manual Adjustment", "2025 Observed Tracy Arm Event (Baseline)", "Maximum Credible Failure (Worst-Case)", "Minor Localized Slope Detachment"]
    )

    # Initialize session state keys if not present
    for k in ["vol", "mass", "vel", "thick", "width", "angle", "depth", "radius"]:
        if k not in st.session_state:
            st.session_state[k] = 5.0e7 if k == "vol" else 1.0e10 if k == "mass" else 40.0 if k == "vel" else 80.0 if k == "thick" else 500.0 if k == "width" else 45.0 if k == "angle" else 300.0 if k == "depth" else 500.0

    # Update keys if preset selected (and not manual)
    if scenario_preset != "Manual Adjustment":
        preset_vals = PRESETS[scenario_preset]
        for k, v in preset_vals.items():
            st.session_state[k] = v

    st.subheader("Landslide Parameters")
    volume = st.number_input(
        "Volume (m³) — [1M: Minor | 50M: 2025 Historic Event | 150M+: Catastrophic]", 
        1e6, 5e9, step=1e6, format="%.0f", key="vol"
    )
    mass = st.number_input(
        "Mass (kg) — [1B: Minor | 100B: 2025 Historic Event | 1T+: Catastrophic]", 
        1e9, 5e12, step=1e9, format="%.0f", key="mass"
    )
    velocity = st.number_input(
        "Impact velocity (m/s) — [10m/s: Slow | 40m/s: Historic | 100m/s+: High-speed]", 
        5.0, 120.0, step=1.0, key="vel"
    )
    thickness = st.number_input(
        "Slide thickness (m) — [10m: Thin slump | 75m: Historic | 200m+: Deep collapse]", 
        10.0, 500.0, step=5.0, key="thick"
    )
    width = st.number_input(
        "Slide width (m)", 
        50.0, 2000.0, step=10.0, key="width"
    )
    angle = st.number_input(
        "Slope Angle at Shoreline Intersection (deg) — [Sub-30°: Gradual Slump | 45°: Average | 70°+: Vertical Cliff]", 
        10.0, 80.0, step=1.0, key="angle"
    )

with col2:
    st.subheader("Target Impact Boundary Zone")
    impact_zone = st.selectbox(
        "Select Landslide Source Wall:",
        ["South Sawyer Glacier Face (2025 Collapse Site)", "North Fjord Entrance Cliff Face", "Mid-Channel Operational Transit Corridor", "Manual Coordinate Selection"]
    )

    if impact_zone == "South Sawyer Glacier Face (2025 Collapse Site)":
        x0 = 454
        y0 = 474
    elif impact_zone == "North Fjord Entrance Cliff Face":
        x0 = 200
        y0 = 300
    elif impact_zone == "Mid-Channel Operational Transit Corridor":
        x0 = 600
        y0 = 500
    else:
        x0 = st.slider("Impact X position (index)", 0, X.shape[1] - 1, X.shape[1] // 2)
        y0 = st.slider("Impact Y position (index)", 0, X.shape[0] - 1, X.shape[0] // 2)

    depth_at_impact = st.number_input(
        "Water depth at impact (m)", 
        50.0, 1000.0, step=10.0, key="depth"
    )
    radius = st.number_input(
        "Impact radius (m) — [50m: Localized | 200m: Standard | 500m+: Large-scale]", 
        50.0, 1000.0, key="radius", step=10.0
    )

with col2:
    st.write("")
    with st.expander("📘 Understanding the Physics of Landslide Impulse Waves"):
        st.markdown("""
        The initial height of the tsunami wave ($η_0$) is determined by the **Heller–Hager–Fritz (HHF) Impulse Product Parameter**. 
        
        Here is how your inputs directly drive the wave dynamics:
        * **The Power of Thickness:** Wave height scales heavily with **Slide Thickness**. A thick, consolidated block displacement generates a significantly larger impulse wave than a thin, scattered rock shower of the same total volume.
        * **The Velocity Factor:** Kinetic energy scales quadratically with speed. Higher **Impact Velocities** push water outward with exponentially greater force.
        * **The Slope Angle Paradox:** Steeper impact angles (near 90°) convert horizontal landslide momentum into massive vertical kinetic run-up energy along the opposite shorelines.
        """)

slide = SlideParameters(
    volume=volume,
    mass=mass,
    impact_velocity=velocity,
    thickness=thickness,
    width=width,
    impact_angle_deg=angle,
)

water = WaterColumnParameters(depth_at_impact=depth_at_impact)

# Check if coordinate is in the water (Z < 0 and not masked)
is_water = False
if not np.ma.is_masked(Z[y0, x0]):
    if Z[y0, x0] < 0:
        is_water = True

if not is_water:
    # Snap to the nearest water cell (where Z < 0 and Z is not masked)
    water_indices = np.where((Z < 0) & (~np.ma.getmaskarray(Z)))
    if len(water_indices[0]) > 0:
        distances = (water_indices[1] - x0)**2 + (water_indices[0] - y0)**2
        nearest_idx = np.argmin(distances)
        y0_active = water_indices[0][nearest_idx]
        x0_active = water_indices[1][nearest_idx]
    else:
        y0_active, x0_active = y0, x0
else:
    y0_active, x0_active = y0, x0

# Compute initial wave centered at the active (snapped) water cell
impact_center = (X[y0_active, x0_active], Y[y0_active, x0_active])
eta0 = apply_eta0_to_mesh(X, Y, Z, impact_center, slide, water, radius=radius)
st.session_state["eta0"] = eta0
st.session_state["impact_x0"] = x0_active
st.session_state["impact_y0"] = y0_active
eta0_max = compute_initial_wave_amplitude(slide, water)

# Real-time metrics and dynamic feedback
col_stats1, col_stats2 = st.columns(2)
with col_stats1:
    st.metric(
        label="Peak Initial Wave Amplitude (η₀)",
        value=f"{eta0_max:.2f} meters"
    )
with col_stats2:
    st.info("💡 **State Synchronized:** The initial wave (η₀) and map visualization update automatically whenever parameters or sliders change. The updated wave field is saved to session state for the simulation solver.")

# Always display the geographical alignment and initial wave plot
st.subheader("Geographically Aligned Initial Wave (η₀)")
try:
    # Use Z (the flipped structured mesh) as the background
    if hasattr(Z, "filled"):
        Z_filled = Z.filled(0.0)
    else:
        Z_filled = np.asarray(Z)
        
    # Crop the mesh to focus on the active landslide and wave propagation zone (zoom-in)
    # This visually excludes the non-impacted areas (like Holkham Bay)
    i_start, i_end = 330, 540   # Range: 9900m to 16200m Easting
    j_start, j_end = 360, 590   # Range: 10800m to 17700m Northing
    stride = 1                  # Stride = 1 (full resolution) because the cropped region is small and fast
    
    geo_cropped = Z_filled[j_start:j_end, i_start:i_end]
    geo_background = geo_cropped[::stride, ::stride]
    
    eta0_full = st.session_state.get("eta0")

    # Calculate exact coordinates for the cropped and downsampled mesh
    x_meters = (i_start + np.arange(geo_background.shape[1]) * stride) * 30.0
    y_meters = (j_start + np.arange(geo_background.shape[0]) * stride) * 30.0

    fig = go.Figure()

    # Layer A: Plot the true fjord geometry as a grayscale/muted contour map (full resolution)
    fig.add_trace(go.Contour(
        x=x_meters,
        y=y_meters,
        z=geo_background,
        colorscale='Greys',
        showscale=False,
        opacity=0.25,
        hoverinfo='skip',
        name="Fjord Topography"
    ))

    # Layer B: Overlay the generated impulse wave pulse over the terrain map (only if generated)
    if eta0_full is not None:
        eta_cropped = eta0_full[j_start:j_end, i_start:i_end]
        eta_0 = eta_cropped[::stride, ::stride]
        # Mask values close to 0 to NaN to make them transparent
        eta_0 = np.where(np.abs(eta_0) < 0.01, np.nan, eta_0)
        
        if not np.all(np.isnan(eta_0)):
            fig.add_trace(go.Contour(
                x=x_meters,
                y=y_meters,
                z=eta_0,
                colorscale='Viridis',
                line_width=0,
                ncontours=15,
                colorbar=dict(
                    title=dict(text="Wave Height η₀ (m)", side="right")
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
    fig.add_trace(go.Scatter(
        x=[x0_active * 30.0],
        y=[y0_active * 30.0],
        mode='markers+text',
        marker=dict(color='crimson', size=14, symbol='x', line=dict(width=2, color='white')),
        text=['<b>❌ Slide Impact Center</b>'],
        textposition='top center',
        textfont=dict(size=12, color='#b91c1c', family='Arial, sans-serif'),
        showlegend=False,
        name='Landslide Entry Site'
    ))

    fig.update_layout(
        title="Geographically Anchored Scenario Stress-Test (Initial Wave Status)",
        xaxis_title="UTM Zone 8N Easting Offset (Relative Meters)",
        yaxis_title="UTM Zone 8N Northing Offset (Relative Meters)",
        template="plotly_dark",
        xaxis=dict(range=[i_start * 30.0, i_end * 30.0], showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(range=[j_start * 30.0, j_end * 30.0], showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)

except FileNotFoundError:
    st.error("Please run the data processor pipeline before configuring the impulse wave.")
