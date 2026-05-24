import streamlit as st
import plotly.express as px
import numpy as np
from energy.ontario_grid_twin.src.utils.ui_branding import apply_branding
from energy.ontario_grid_twin.src.engine.grid_classifier import add_grid_classification

apply_branding()

if 'data_loaded' not in st.session_state:
    st.error("Please return to the [Home Page](../app.py) to initialize the application data.")
    st.stop()

subs = st.session_state['subs']
grid_nodes = st.session_state['grid_nodes']

# Ensure classification is active
if 'grid_centre_type' not in subs.columns:
    subs = add_grid_classification(subs)

st.markdown("## 🎲 Grid Reliability Analysis (Monte Carlo Analysis)")
st.markdown("##### Probabilistic Distribution of Grid Load Scenarios")
st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Simulation Parameters")
    region_options = sorted(subs['region'].dropna().astype(str).unique())
    selected_region = st.selectbox("Region", region_options, key="mc_region")

    # Filter options by region and exclude Demand Centres
    subs_filtered = subs[
        (subs['region'].astype(str) == selected_region) & 
        (subs['grid_centre_type'].isin(["Transmission Substation", "Regional Transformer Station"]))
    ]
    
    if subs_filtered.empty:
        st.warning(f"No Transmission or Regional stations found in {selected_region}.")
        st.stop()

    target_level = st.radio(
        "Select Infrastructure Level", 
        ["Transmission Substation", "Regional Transformer Station"],
        index=0,
        key="mc_level"
    )
    
    level_candidates = subs_filtered[subs_filtered['grid_centre_type'] == target_level]
    
    if level_candidates.empty:
        st.warning(f"No {target_level}s in {selected_region}.")
        st.stop()

    target_options = sorted(level_candidates['name'].dropna().astype(str).unique())
    target_sub = st.selectbox("Select Target Node", target_options, key="mc_sub")
    
    dc_load = st.slider("Simulated Data Centre Load (MW)", 0, 600, 100, key="mc_slider")
    iterations = st.slider("Simulation Iterations", 1000, 10000, 5000, step=1000)
    
    node = grid_nodes[target_sub]
    simulated_loads = node.simulate_loads(new_load_mw=dc_load, iterations=iterations)
    reliability = (np.sum(simulated_loads <= node.capacity_mw) / iterations) * 100
    
    st.markdown("---")
    st.markdown(f"**Target Node:** `{target_sub}`")
    st.markdown(f"**Base Capacity:** `{node.capacity_mw} MW`")
    st.markdown(f"**Proposed Load:** `+{dc_load} MW`")
    st.markdown(f"**Reliability Probability:** `{reliability:.2f}%`")
    
    if reliability < 100:
        st.warning(f"**Risk Detected:** There is a `{100-reliability:.2f}%` chance that the grid will exceed maximum capacity under peak conditions.")
    else:
        st.success("**Safe:** The grid is projected to handle the load without exceeding capacity under all simulated scenarios.")
        
with col2:
    fig = px.histogram(
        x=simulated_loads, 
        nbins=50, 
        title=f"Load Distribution for {target_sub} (+ {dc_load} MW)",
        labels={'x': 'Total Projected Load (MW)', 'y': 'Frequency (Scenarios)'},
        color_discrete_sequence=['#1f77b4']
    )
    fig.add_vline(x=node.capacity_mw, line_dash="dash", line_color="red", 
                  annotation_text=f"Max Capacity ({node.capacity_mw} MW)", annotation_position="top right")
    fig.update_layout(xaxis_title="Total Projected Load (MW)", yaxis_title="Frequency")
    st.plotly_chart(fig, use_container_width=True)
