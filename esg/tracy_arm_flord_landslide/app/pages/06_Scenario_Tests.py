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
from src.engines.hhf import (
    SlideParameters,
    WaterColumnParameters,
    compute_initial_wave_amplitude,
)

st.set_page_config(page_title="What-If Analysis & Scenario Tests", layout="wide")

st.title("🎛️ What-If Analysis & Scenario Tests")
st.markdown("""
Evaluate the vulnerability of vessel traffic and maritime operations within Tracy Arm Fjord under different landslide and climate-risk scenarios.
This page lets you run **what-if sweeps** and model **cruise ship hazard exposure** profiles.
""")

# Load the geospatial mesh for coordinate calculations
dem, x_dem, y_dem = load_tracy_arm_dem()
X, Y, Z = build_structured_mesh(dem, x_dem, y_dem)

# Initialize session state keys if not present (falls back to baseline event defaults)
for k in ["vol", "mass", "vel", "thick", "width", "angle", "depth", "radius"]:
    if k not in st.session_state:
        st.session_state[k] = 5.5e7 if k == "vol" else 1.1e11 if k == "mass" else 40.0 if k == "vel" else 75.0 if k == "thick" else 500.0 if k == "width" else 42.0 if k == "angle" else 300.0 if k == "depth" else 500.0

# Slide entry center coordinates
x0_active = st.session_state.get("impact_x0", 454)
y0_active = st.session_state.get("impact_y0", 474)
x_origin = x0_active * 30.0
y_origin = y0_active * 30.0

st.subheader("1. Cruise Ship Risk Exposure Calculator")
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### Configure Vessel Position")
    preset_location = st.selectbox(
        "Choose Predefined Location:",
        ["Cruise Ship Transit Lane (10.5 km)", "Outer Fjord Entrance (22.0 km)", "Sawyer Island Corridor (4.8 km)", "Custom Coordinates"]
    )
    
    if preset_location == "Cruise Ship Transit Lane (10.5 km)":
        x_ship = 10200.0
        y_ship = 11000.0
    elif preset_location == "Outer Fjord Entrance (22.0 km)":
        x_ship = 3000.0
        y_ship = 6000.0
    elif preset_location == "Sawyer Island Corridor (4.8 km)":
        x_ship = 12000.0
        y_ship = 11500.0
    else:
        # Custom coordinates inputs bounded within the mesh
        x_ship = st.number_input("Vessel Easting Coordinate (X, m)", float(X.min()), float(X.max()), 10200.0, step=100.0)
        y_ship = st.number_input("Vessel Northing Coordinate (Y, m)", float(Y.min()), float(Y.max()), 11000.0, step=100.0)

    # Calculate distance to slide origin
    distance = np.sqrt((x_ship - x_origin)**2 + (y_ship - y_origin)**2)
    st.metric("Distance to Slide Impact site", f"{distance/1000.0:.2f} km")
    results_container = st.container()

with col2:
    st.markdown("### Landslide Source Magnitude")
    
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

    scenario_preset = st.selectbox(
        "Choose Landslide Scenario Preset:",
        ["Manual Adjustment", "2025 Observed Tracy Arm Event (Baseline)", "Maximum Credible Failure (Worst-Case)", "Minor Localized Slope Detachment"],
        key="preset_scenario_tests"
    )

    if scenario_preset != "Manual Adjustment":
        preset_vals = PRESETS[scenario_preset]
        for k, v in preset_vals.items():
            st.session_state[k] = v

    col_v, col_t = st.columns(2)
    with col_v:
        volume = st.number_input(
            "Landslide Volume (m³) — [1M: Minor | 50M: 2025 Historic Event | 150M+: Catastrophic]",
            1e6, 5e9, key="vol", step=1e6, format="%.0f"
        )
        thickness = st.number_input(
            "Slide Thickness (m) — [10m: Thin slump | 75m: Historic | 200m+: Deep collapse]",
            10.0, 500.0, key="thick", step=5.0
        )
        mass = st.number_input(
            "Slide Mass (kg) — [1B: Minor | 100B: 2025 Historic Event | 1T+: Catastrophic]",
            1e9, 5e12, key="mass", step=1e9, format="%.0f"
        )
        width = st.number_input(
            "Slide Width (m)",
            50.0, 2000.0, key="width", step=10.0
        )
    with col_t:
        velocity = st.number_input(
            "Impact Velocity (m/s) — [10m/s: Slow | 40m/s: Historic | 100m/s+: High-speed]",
            5.0, 120.0, key="vel", step=5.0
        )
        depth_at_impact = st.number_input(
            "Water Depth at Origin (m) — [50m: Shallow | 300m: Mid-fjord | 500m+: Deep]",
            50.0, 1000.0, key="depth", step=10.0
        )
        angle = st.number_input(
            "Slope Angle (deg) — [Sub-30°: Gradual Slump | 45°: Average | 70°+: Vertical Cliff]",
            10.0, 80.0, key="angle", step=1.0
        )
        radius = st.number_input(
            "Impact Radius (m) — [50m: Localized | 200m: Standard | 500m+: Large-scale]",
            50.0, 1000.0, key="radius", step=10.0
        )
    legend_container = st.container()

# Compute HHF initial wave amplitude
slide = SlideParameters(
    volume=volume,
    mass=mass,
    impact_velocity=velocity,
    thickness=thickness,
    width=width,
    impact_angle_deg=angle,
)
water = WaterColumnParameters(depth_at_impact=depth_at_impact)
eta0_max = compute_initial_wave_amplitude(slide, water)

# Estimate average depth along the path to calculate travel celerity
# Map coordinates to indices for depth checking
ship_x_idx = int(np.clip(x_ship / 30.0, 0, Z.shape[1] - 1))
ship_y_idx = int(np.clip(y_ship / 30.0, 0, Z.shape[0] - 1))
ship_depth = -Z[ship_y_idx, ship_x_idx] if Z[ship_y_idx, ship_x_idx] < 0 else 10.0
avg_depth = max(10.0, (depth_at_impact + ship_depth) / 2.0)

# Calculate propagation velocity (celerity) and arrival time
g = 9.81
celerity = np.sqrt(g * avg_depth)
travel_time = distance / celerity

# Calculate wave height at ship using radial decay model: eta(d) = eta0 * sqrt(R0/d)
# where R0 is the landslide impact radius
eta_ship = eta0_max * np.sqrt(radius / max(radius, distance))

# Display results in the left column results container
with results_container:
    st.markdown("---")
    st.markdown(f"### Wave Propagation Output")
    st.markdown(f"#### Wave Travel Time: **{travel_time/60.0:.1f} minutes** ({travel_time:.0f} s)")
    st.markdown(f"#### Estimated Wave Height: **{eta_ship:.2f} meters**")
    st.caption(f"Calculated wave speed celerity: {celerity*3.6:.1f} km/h ({celerity:.1f} m/s) over an average channel depth of {avg_depth:.0f} m.")
    
    if eta_ship < 0.5:
        st.success("🟢 **Hazard Exposure Rating: SAFE**\n\nWave amplitude is under 0.5m. No significant risk of capsizing or structural damage to commercial vessels.")
    elif eta_ship < 1.5:
        st.warning("🟡 **Hazard Exposure Rating: ADVISORY**\n\nWave amplitude between 0.5m and 1.5m. Strong sloshing and rapid local currents expected. Secure loose deck equipment, and advise passengers to stay indoors.")
    elif eta_ship < 3.0:
        st.error("🟠 **Hazard Exposure Rating: HAZARDOUS**\n\nWave amplitude between 1.5m and 3.0m. Severe surges can break mooring lines and threaten smaller vessels. Immediate evacuation of near-shore coordinates is recommended.")
    else:
        st.error("🔴 **Hazard Exposure Rating: CRITICAL THREAT**\n\nWave amplitude exceeds 3.0m. High risk of structural capsizing and cargo damage for all vessel types in the channel. Evacuate transit corridors immediately.")

# Display legend table in the right column legend container
with legend_container:
    st.markdown("---")
    st.markdown("### ℹ️ Maritime Hazard Classification Scale")
    st.markdown("""
| Rating | Wave Height | Expected Impact & Safety Action |
| :--- | :--- | :--- |
| 🟢 **SAFE** | `< 0.5 m` | Minimal wave energy. Normal navigation and vessel operations. |
| 🟡 **ADVISORY** | `0.5 m – 1.5 m` | Strong localized currents/surges. Secure deck cargo, stay clear of low decks. |
| 🟠 **HAZARDOUS** | `1.5 m – 3.0 m` | Severe harbor surges and mooring damage. Evacuate open water corridors and small craft. |
| 🔴 **CRITICAL** | `≥ 3.0 m` | Structural damage & capsize risk for large vessels. Immediate emergency transit evacuation. |
    """)

st.markdown("---")
st.subheader("2. What-If Volume Sweep Analysis")

# Sweep parameter: landslide volume
volumes_sweep = np.linspace(1e6, 1.5e8, 30) # 1M to 150M cubic meters
heights_sweep = []

for vol in volumes_sweep:
    sweep_slide = SlideParameters(
        volume=vol,
        mass=vol * 2000.0, # Approximate mass based on rock density
        impact_velocity=velocity,
        thickness=thickness,
        width=width,
        impact_angle_deg=angle,
    )
    sweep_eta0 = compute_initial_wave_amplitude(sweep_slide, water)
    sweep_eta_ship = sweep_eta0 * np.sqrt(radius / max(radius, distance))
    heights_sweep.append(sweep_eta_ship)

# Plot the risk curve
fig = go.Figure()

# Plot the curve
fig.add_trace(go.Scatter(
    x=volumes_sweep / 1e6,
    y=heights_sweep,
    mode='lines+markers',
    name='Estimated Wave Height',
    line=dict(color='#3b82f6', width=3),
    marker=dict(size=6, color='#1e3a8a'),
    hovertemplate="Slide Volume: %{x:.1f}M m³<br>Wave Height at Vessel: %{y:.2f} m<extra></extra>"
))

# Highlight safety thresholds
fig.add_hline(y=0.5, line_dash="dash", line_color="green", annotation_text="Advisory Threshold (0.5m)", annotation_position="top left")
fig.add_hline(y=1.5, line_dash="dash", line_color="orange", annotation_text="Hazardous Threshold (1.5m)", annotation_position="top left")
fig.add_hline(y=3.0, line_dash="dash", line_color="red", annotation_text="Critical Threat Threshold (3.0m)", annotation_position="top left")

# Highlight current selection
fig.add_trace(go.Scatter(
    x=[volume / 1e6],
    y=[eta_ship],
    mode='markers',
    marker=dict(color='crimson', size=14, symbol='star', line=dict(width=2, color='white')),
    name='Current Scenario',
    hovertemplate="Current Scenario:<br>Volume: %{x:.1f}M m³<br>Wave Height: %{y:.2f} m<extra></extra>"
))

fig.update_layout(
    title=f"Vessel Risk Curve: Wave Height at Ship vs. Landslide Volume (Vessel at {distance/1000.0:.2f} km)",
    xaxis_title="Landslide Failure Volume (Million m³)",
    yaxis_title="Estimated Wave Height at Ship Position (m)",
    template="plotly_dark",
    height=500,
    showlegend=True
)

st.plotly_chart(fig, use_container_width=True)
