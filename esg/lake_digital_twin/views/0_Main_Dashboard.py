import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
# Modular Imports
from models.hydrology_engine import calculate_nutrient_loading, get_runoff_coefficient, build_3d_mesh
from models.chemical_engine import calculate_saturation_index, simulate_lake_stability, virtual_jar_test

st.title("🌊 Lake Health Dashboard")

# ── Lake Context Banner ───────────────────────────────────────────────────────
selected_lake = st.session_state.get("selected_lake")
if selected_lake:
    trophic_icon = {"Oligotrophic": "🔵", "Mesotrophic": "🟢", "Eutrophic": "🔴"}.get(selected_lake["trophic_state"], "⚪")
    st.info(
        f"{trophic_icon} **Analysing: {selected_lake['name']}** — "
        f"{selected_lake['trophic_state']} | {selected_lake['conservation_authority']} | "
        f"Max Depth: {selected_lake['max_depth_m']} m | Catchment: {selected_lake['catchment_area_km2']} km²"
    )
else:
    st.warning("No lake selected. Go to **Location → Lake Selector** to pick an Ontario lake, or adjust parameters manually below.")

# Use lake defaults where available, otherwise use hardcoded defaults
_default_agri = selected_lake['agri_pct'] if selected_lake else 30
_default_ph = selected_lake['ph_baseline'] if selected_lake else 8.1
_default_ca = selected_lake['ca_baseline'] if selected_lake else 40.0

# Initialize session state for Phosphorus if not exists
if 'tp' not in st.session_state:
    st.session_state['tp'] = selected_lake['tp_baseline'] if selected_lake else 0.025

# Sidebar for Project Inputs
with st.sidebar.expander("Project Parameters"):
    rainfall = st.slider("Rainfall Event (mm)", 0, 150, 25)
    agri_land = st.slider("Agricultural Land (%)", 0, 100, _default_agri)
    st.markdown("---")

with st.sidebar.expander("Water Chemistry"):
    ph = st.slider("pH Level", 6.5, 9.5, _default_ph)
    ca = st.number_input("Calcium (mg/L)", value=_default_ca)
    # Use session state for Phosphorus value
    tp = st.number_input("Total Phosphorus (mg/L)", value=st.session_state['tp'], format="%.3f")

    st.markdown("---")
with st.sidebar.expander("🧪 Virtual Jar Test"):
    # st.subheader("🧪 Virtual Jar Test")
    st.write("Simulate chemical dosing to reduce Phosphorus.")
    
    # Input for chemical dosage
    ca_dose = st.slider("Calcium Dosage (mg/L)", 0, 100, 10)
    
    # Run the simulation engine
    final_p, pct_removed = virtual_jar_test(tp, ca_dose, ph)
    
    st.info(f"Predicted TP: {final_p:.3f} mg/L")
    st.success(f"Removal Efficiency: {pct_removed:.1f}%")
    
    if st.button("Apply Dose to Model"):
        # Update session state and rerun to refresh the dashboard with new TP
        st.session_state['tp'] = final_p
        st.rerun()

# --- EXECUTION LOGIC ---
c_factor = get_runoff_coefficient(agri_land)
influent_vol = calculate_nutrient_loading(rainfall, 50, c_factor)
si_result = calculate_saturation_index(ph, ca, tp)
status, color = simulate_lake_stability(tp, ca)

# --- DISPLAY UI ---
col1, col2 = st.columns([1, 2])

with col1:
    st.metric("Estimated Influent Volume", f"{influent_vol:,.0f} m³")
    st.markdown("---")
    st.subheader("Stability Analysis")
    st.markdown(f"**State:** :{color}[{status}]")
    st.markdown(f"**Saturation Index (SI):** {si_result}")
    
    if si_result > 0:
        st.success("Chemistry suggests natural phosphorus precipitation.")
    else:
        st.error("Chemistry suggests phosphorus remains bioavailable for algae.")

with col2:
    st.subheader("3D Bathymetry & Hypoxia Model")
    # Synthetic Bathymetry Data (Replace with CSV upload in Phase 4)
    np.random.seed(42) 
    obs_data = pd.DataFrame({
        'x': np.random.uniform(0, 100, 50),
        'y': np.random.uniform(0, 100, 50),
        'depth': -np.random.uniform(5, 40, 50)
    })
    
    gx, gy, gz = build_3d_mesh(obs_data)
    
    fig = go.Figure(data=[go.Surface(z=gz, x=gx, y=gy, colorscale='Viridis')])
    
    # Visualization of the Hypoxic "Dead Zone" (e.g., depths > 25m)
    fig.add_trace(go.Surface(z=np.full_like(gz, -25), x=gx, y=gy, 
                             showscale=False, opacity=0.3, colorscale='Reds'))
    
    fig.update_layout(title="3D Bathymetry & Hypoxia Model", margin=dict(l=0, r=0, b=0, t=40))
    st.plotly_chart(fig, width="stretch")


# Inside your main app's display section
st.markdown("---")
st.subheader("Virtual Jar Test Results")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.metric("Baseline Phosphorus", f"{tp:.3f} mg/L")
    st.caption("Current Lake State")

with col2:
    # Display the result from the Jar Test simulation
    st.metric("Treated Phosphorus", f"{final_p:.3f} mg/L", 
              delta=f"-{pct_removed:.1f}%", delta_color="normal")
    st.caption(f"After {ca_dose} mg/L Calcium Dose")

st.info("**Notes:** This model applies Mass Balance and Stumm-Morgan equilibrium for real-time environmental assessment.")

