import sys
from pathlib import Path

# Add the directory containing the 'energy' folder to sys.path
current_dir = Path(__file__).resolve().parent
while current_dir.name and not (current_dir / "energy").exists():
    if current_dir == current_dir.parent:
        break
    current_dir = current_dir.parent

if (current_dir / "energy").exists() and str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import streamlit as st
import pandas as pd
import pydeck as pdk
from energy.ontario_grid_twin.src.engine.data_loader import load_base_grid
from energy.ontario_grid_twin.src.engine.grid_classifier import add_grid_classification
from energy.ontario_grid_twin.src.utils.york_capacity_analysis import analyze_york_capacity
from energy.ontario_grid_twin.src.engine.ieso_harvester import IESOHarvester
from scipy.spatial import KDTree
import numpy as np

st.set_page_config(page_title="Grid Centres", layout="wide")

st.markdown("## 🏢 Grid Centres")
st.markdown("##### Detailed Classification of Ontario's Transmission and Regional Infrastructure")
st.markdown("""
This page identifies grid centres by **Transmission Substation**, **Regional Transformer Station (TS)**, and **Demand Centres (Distribution)**.
It also highlights stations in the **York Region** that are approaching their thermal capacity limits.
""")

# --- LIVE DATA HEADER ---
live_demand = IESOHarvester.get_latest_demand()
if live_demand:
    st.info(f"🌐 **Live IESO Status:** Provincial Demand is currently **{live_demand['demand_mw']:,} MW** (As of {live_demand['timestamp']})")

# Load data
subs, lines, gen, dc = load_base_grid()

# Explicitly re-run classification to ensure latest logic is applied
subs = add_grid_classification(subs)

# Integrate Data Centres as Demand Centres
if dc is not None and not dc.empty:
    dc_demand = dc.copy()
    dc_demand['grid_centre_type'] = "Demand Centre (Distribution)"
    dc_demand['voltage'] = "Low Voltage (LV)"
    dc_demand['current_load_mw'] = dc_demand['load_mw']
    
    # Combine with substations for a complete hierarchy view
    subs = pd.concat([subs, dc_demand], ignore_index=True)

# --- NETWORK TOPOLOGY & LOAD BALANCING ---
# Logic: Orange (Regional TS) load = Sum of all connected Green (Demand Centres)
regional_ts = subs[subs['grid_centre_type'] == "Regional Transformer Station"].copy()
demand_centres = subs[subs['grid_centre_type'] == "Demand Centre (Distribution)"].copy()

if not regional_ts.empty and not demand_centres.empty:
    # Build KDTree for nearest neighbour search
    tree = KDTree(regional_ts[['lon', 'lat']].values)
    dist, indices = tree.query(demand_centres[['lon', 'lat']].values)
    
    # Map connections
    demand_centres['parent_ts_index'] = indices
    demand_centres['parent_ts_name'] = regional_ts.iloc[indices]['name'].values
    
    # Aggregate load at Regional TS level
    ts_load_sums = demand_centres.groupby('parent_ts_index')['current_load_mw'].sum()
    
    # Update Regional TS loads based on the sum of children
    for ts_idx, load_sum in ts_load_sums.items():
        subs.loc[regional_ts.index[ts_idx], 'current_load_mw'] = load_sum

    # Prepare connection lines for pydeck
    connection_lines = []
    for _, dc_row in demand_centres.iterrows():
        parent = regional_ts.iloc[int(dc_row['parent_ts_index'])]
        connection_lines.append({
            "start": [dc_row['lon'], dc_row['lat']],
            "end": [parent['lon'], parent['lat']],
            "name": f"{dc_row['name']} -> {parent['name']}"
        })
    connection_df = pd.DataFrame(connection_lines)
else:
    connection_df = pd.DataFrame()

# Classification Sidebar
st.sidebar.header("Map Filters")

# Region Filter
all_regions = sorted(subs['region'].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect("Select Regions", all_regions, default=all_regions)

# Type Filter
centre_types = subs['grid_centre_type'].unique().tolist()
selected_types = st.sidebar.multiselect("Select Centre Types", centre_types, default=centre_types)

# Apply filters
filtered_subs = subs[
    (subs['grid_centre_type'].isin(selected_types)) & 
    (subs['region'].isin(selected_regions))
]

# Map Visuals
st.subheader("Ontario Grid Hierarchy")

with st.expander("🔍 View Data Classification Sample"):
    st.write("Below is a sample of how substations are currently being categorized:")
    st.dataframe(subs[['name', 'voltage', 'grid_centre_type']].head(10))

# Colour map for centre types
COLOR_MAP = {
    "Transmission Substation": [255, 0, 0, 200],      # Red
    "Regional Transformer Station": [255, 165, 0, 200], # Orange
    "Demand Centre (Distribution)": [0, 128, 0, 200]   # Green
}

filtered_subs['color'] = filtered_subs['grid_centre_type'].apply(lambda x: COLOR_MAP.get(x, [200, 200, 200, 200]))

layer = pdk.Layer(
    "ScatterplotLayer",
    filtered_subs,
    get_position=["lon", "lat"],
    get_color="color",
    get_radius=2000,
    pickable=True,
)

# Line layer for TS-Demand connections
line_layer = pdk.Layer(
    "LineLayer",
    connection_df,
    get_source_position="start",
    get_target_position="end",
    get_color=[255, 165, 0, 100], # Faded orange
    get_width=2,
    pickable=True,
)

view_state = pdk.ViewState(latitude=44.0, longitude=-79.4, zoom=8, pitch=50)

st.pydeck_chart(pdk.Deck(
    layers=[line_layer, layer],
    initial_view_state=view_state,
    tooltip={"text": "{name}\nType: {grid_centre_type}\nLoad: {current_load_mw} MW"}
))

# York Region Analysis
st.divider()
st.subheader("📍 York Region Capacity Analysis")

col1, col2 = st.columns([1, 2])

with col1:
    threshold = st.slider("Capacity Threshold (%)", 50, 100, 80) / 100
    critical_subs = analyze_york_capacity(threshold=threshold)
    
    if critical_subs is not None and not critical_subs.empty:
        st.warning(f"Found {len(critical_subs)} stations above {threshold*100:.0f}% capacity.")
        st.dataframe(critical_subs[['name', 'voltage', 'load_factor']].style.format({'load_factor': '{:.2%}'}))
    else:
        st.success(f"No stations above {threshold*100:.0f}% capacity found.")

with col2:
    if critical_subs is not None and not critical_subs.empty:
        # Highlight critical stations on a mini map
        critical_subs['color'] = [[255, 0, 0, 255]] * len(critical_subs) # Bright red for critical
        
        critical_layer = pdk.Layer(
            "ScatterplotLayer",
            critical_subs,
            get_position=["lon", "lat"],
            get_color="color",
            get_radius=3000,
            pickable=True,
        )
        
        st.pydeck_chart(pdk.Deck(
            layers=[critical_layer],
            initial_view_state=pdk.ViewState(latitude=44.0, longitude=-79.4, zoom=9),
            tooltip={"text": "{name}\nLoad: {load_factor:.1%}"}
        ))
    else:
        st.info("Adjust the threshold to see station loading in York Region.")

# Legend
st.sidebar.markdown("---")
st.sidebar.markdown("**Legend**")

# Calculate counts for each type in the filtered view
type_counts = filtered_subs['grid_centre_type'].value_counts().to_dict()

for k, v in COLOR_MAP.items():
    count = type_counts.get(k, 0)
    st.sidebar.markdown(f"<span style='color:rgb({v[0]},{v[1]},{v[2]})'>●</span> {k} (**{count}**)", unsafe_allow_html=True)
