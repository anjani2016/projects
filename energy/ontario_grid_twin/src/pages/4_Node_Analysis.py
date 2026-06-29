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
import pydeck as pdk
import pandas as pd
import numpy as np
from energy.ontario_grid_twin.src.utils.ui_branding import apply_branding
from energy.ontario_grid_twin.src.engine.ieso_harvester import IESOHarvester
from energy.ontario_grid_twin.src.engine.grid_classifier import add_grid_classification

apply_branding()

# ── Constants (import from data_loader so colours stay in sync) ───────────────
from energy.ontario_grid_twin.src.engine.data_loader import GENERATION_CATEGORIES, GENERATION_CATEGORY_COLORS

# ── Guard: data must be initialised in app.py ─────────────────────────────────
if 'data_loaded' not in st.session_state:
    st.error("Please return to the [Home Page](../app.py) to initialise the application data.")
    st.stop()

# ── Retrieve shared data ───────────────────────────────────────────────────────
subs       = st.session_state['subs']
gen        = st.session_state['gen']
dc         = st.session_state['dc']
grid_nodes = st.session_state['grid_nodes']

# Ensure classification is active (safety check for session persistence)
if 'grid_centre_type' not in subs.columns:
    subs = add_grid_classification(subs)

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("## ⚡ Node Analysis: Ontario Grid Digital Twin")
st.markdown("##### Substation Simulation: Evaluating 2026 IESO Forecasts for Provincial Infrastructure.")
st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
# ── Substation region filter (used to scope substations and generation) ───────
all_sub_regions = sorted(subs['region'].dropna().astype(str).unique())
selected_sub_regions = st.sidebar.multiselect(
    "Substation Regions",
    all_sub_regions,
    default=all_sub_regions,
    help="Filters substations and generation sources to the same selected regions.",
)

subs_filtered = subs[subs['region'].isin(selected_sub_regions)] if selected_sub_regions else subs.iloc[0:0]
if subs_filtered.empty:
    st.warning("No substations found for the selected region filter.")
    st.stop()

gen_filtered = gen
if gen is not None and 'region' in gen.columns and selected_sub_regions:
    gen_filtered = gen[gen['region'].isin(selected_sub_regions)]

# ── Generation source category filters (placed above simulation controls) ─────
_CAT_EMOJI = {
    "Nuclear":   "🟣",
    "Hydro":     "🔵",
    "Fossil":    "🟠",
    "Renewable": "🟢",
    "Storage":   "🟤",
}

_cat_capacity_mw = {}
for cat in GENERATION_CATEGORIES:
    _cat_capacity_mw[cat] = (
        gen_filtered.loc[gen_filtered['category'] == cat, 'capacity_mw'].sum()
        if gen_filtered is not None else 0
    )

def _kw_to_mw_day(value_kw: float) -> float:
    return value_kw / 1000

_preselected_categories = {
    cat for cat in GENERATION_CATEGORIES if st.session_state.get(f"gen_cat_{cat}", True)
}
_preselected_total_mw = sum(_cat_capacity_mw.get(cat, 0) for cat in _preselected_categories)

# ── Simulation parameters ──────────────────────────────────────────────────────
st.sidebar.header("Simulation Parameters")

# Filter out Demand Centres as targets (only Transmission and Regional are valid for high-load simulation)
valid_targets = subs_filtered[subs_filtered['grid_centre_type'].isin(["Transmission Substation", "Regional Transformer Station"])]

if valid_targets.empty:
    st.sidebar.warning("No Transmission or Regional stations in this region.")
    st.stop()

st.sidebar.header("Simulation Parameters")
st.sidebar.markdown("---")
target_level = st.sidebar.radio(
    "Select Infrastructure Level", 
    ["Transmission Substation", "Regional Transformer Station"],
    index=0
)

# Filter candidates and add Regional context to the names for clarity
level_candidates = valid_targets[valid_targets['grid_centre_type'] == target_level].copy()

if level_candidates.empty:
    st.sidebar.warning(f"No {target_level}s in {', '.join(selected_sub_regions)}")
    st.stop()

# Create a display name: "Region - Station Name" for clarity in each region selection
level_candidates['display_name'] = level_candidates['region'] + " - " + level_candidates['name']

target_sub_display = st.sidebar.selectbox(
    "Select Target Node", 
    level_candidates['display_name'].unique(),
    help=f"Showing all {target_level} assets in selected regions."
)

# Extract original name for calculation
target_sub = target_sub_display.split(" - ", 1)[1] if target_sub_display else level_candidates['name'].iloc[0]
dc_load    = st.sidebar.slider("Simulated Data Centre Load (MW)", 0, 600, 100)
sim_ev_load = st.sidebar.slider("Simulated EV Charger Load (MW)", 0, 400, 40)

# ── Generation source category filters ─────────────────────────────────────────
st.sidebar.header(
    f"Generation Sources - capacity {_kw_to_mw_day(_preselected_total_mw):,.1f} MW/day"
)

selected_categories: set[str] = set()
for cat in GENERATION_CATEGORIES:
    emoji = _CAT_EMOJI.get(cat, "⚪")
    cat_mw_day = _kw_to_mw_day(_cat_capacity_mw.get(cat, 0))
    checked = st.sidebar.checkbox(
        f"{emoji} {cat} ({cat_mw_day:,.1f} MW/day)",
        value=(cat in _preselected_categories),
        key=f"gen_cat_{cat}",
    )
    if checked:
        selected_categories.add(cat)

# ── Map layer toggles ──────────────────────────────────────────────────────────
st.sidebar.header("Map Layers")

# Filter DC by region for consistency
dc_filtered = dc[dc['region'].isin(selected_sub_regions)] if (dc is not None and 'region' in dc.columns) else dc

show_subs  = st.sidebar.toggle(f"Substations ({len(subs_filtered)})",         value=True)

# Count generation sources based on selected regions and categories
visible_gen_count = 0
if gen_filtered is not None:
    visible_gen_count = len(gen_filtered[gen_filtered['category'].isin(selected_categories)])
show_gen   = st.sidebar.toggle(f"Generation Sources ({visible_gen_count})",  value=True)

show_dc    = st.sidebar.toggle(f"Existing Data Centres ({len(dc_filtered) if dc_filtered is not None else 0})", value=False)
show_ev    = st.sidebar.toggle("EV Charger Demand (Estimated)", value=True)
show_flow  = st.sidebar.toggle("Network Flow (Arcs)", value=True)

# ── Live Data Toggle ───────────────────────────────────────────────────────────
st.sidebar.header("Data Sources")
use_live_data = st.sidebar.toggle("Use Live IESO Data", value=False, help="Fetches real-time generation and demand from IESO public reports.")

if use_live_data:
    live_gen = IESOHarvester.get_mapped_gen_data()
    live_demand = IESOHarvester.get_latest_demand()
    
    if live_gen and live_demand:
        st.sidebar.success("Live Data Active")
        with st.sidebar.expander("📊 Real-Time Grid Status", expanded=True):
            st.metric("Provincial Demand", f"{live_demand['demand_mw']:,} MW")
            st.write(f"**Hour:** {live_gen['hour']} | **As of:** {live_gen['timestamp']}")
            for cat, val in live_gen['mapped_data'].items():
                if val > 0:
                    st.write(f"- {cat}: {val:,} MW")
    else:
        st.sidebar.error("Failed to fetch live data. Falling back to demo data.")
        use_live_data = False

# ── Base-map style ─────────────────────────────────────────────────────────────
st.sidebar.header("Base Map")
map_theme = st.sidebar.selectbox(
    "Geography Layer Style",
    ["Dark (Default)", "Streets/Places", "Satellite", "Light"]
)
_THEME_MAP = {
    "Dark (Default)": "dark",
    "Streets/Places": "road",
    "Satellite":      "satellite",
    "Light":          "light",
}

# ══════════════════════════════════════════════════════════════════════════════
# NODE CALCULATIONS
# ══════════════════════════════════════════════════════════════════════════════
sub_info = subs_filtered[subs_filtered['name'] == target_sub].iloc[0]
node     = grid_nodes[target_sub]

# Demo planning approximation:
# EV charging demand is estimated from regional population and a planning-factor
# proxy (kW/day per resident), then distributed across substations in-region.
_REGION_POPULATION = {
    "Toronto": 3026000,
    "York": 1230000,
    "Durham": 770000,
    "Niagara": 500000,
    "Eastern": 1300000,
    "Ottawa Valley": 420000,
    "Northern": 800000,
    "Northwestern": 230000,
    "GTA West": 1100000,
    "Southwest": 1900000,
    "Bruce": 175000,
    "Simcoe": 580000,
    "Central": 950000,
}
_EV_KW_PER_PERSON_DAY = 0.18
ev_region_load_mw = {
    region: (pop * _EV_KW_PER_PERSON_DAY) / 1000
    for region, pop in _REGION_POPULATION.items()
}
target_region = str(sub_info.get("region", "Central"))
target_region_sub_count = max(1, int((subs_filtered["region"] == target_region).sum()))
baseline_ev_per_sub_mw = ev_region_load_mw.get(target_region, 0.0) / target_region_sub_count
effective_ev_load_mw = baseline_ev_per_sub_mw + sim_ev_load
total_new_load_mw = dc_load + effective_ev_load_mw

reliability     = node.calculate_reliability(new_load_mw=total_new_load_mw, iterations=1000)
losses          = node.estimate_losses(load_mw=total_new_load_mw)
remaining_headroom = (
    sub_info.get('headroom_mw', node.capacity_mw - node.base_load_mw) - total_new_load_mw
)

if reliability >= 99:
    status, color_text = "EXCELLENT", "Green Zone"
elif reliability >= 90:
    status, color_text = "FEASIBLE",  "Requires IESO connection assessment"
else:
    status, color_text = "HIGH RISK", "Transformer upgrade likely required"

# ══════════════════════════════════════════════════════════════════════════════
# BUILD MAP LAYERS
# ══════════════════════════════════════════════════════════════════════════════
map_layers: list = []

# ── Helper: substation reliability colour ─────────────────────────────────────
def _sub_color(sub_name: str) -> list[int]:
    n = grid_nodes.get(sub_name)
    if not n:
        return [150, 150, 150, 150]
    rel = n.calculate_reliability(new_load_mw=total_new_load_mw, iterations=200)
    if rel >= 99:   return [0,   255,   0, 180]
    elif rel >= 90: return [255, 165,   0, 200]
    else:           return [255,   0,   0, 200]

subs_display          = subs_filtered.copy()
subs_display['color'] = subs_display['name'].apply(_sub_color)
subs_display["ev_load_mw"] = (
    subs_display["region"].map(lambda r: ev_region_load_mw.get(str(r), 0.0))
    / subs_display.groupby("region")["region"].transform("count")
)
subs_display["ev_load_mw"] = subs_display["ev_load_mw"].fillna(0.0)
subs_display.loc[subs_display["name"] == target_sub, "ev_load_mw"] += sim_ev_load

# Calculate viability counts for the legend
def _get_viability(color):
    if color == [0, 255, 0, 180]: return "Green"
    if color == [255, 165, 0, 200]: return "Orange"
    if color == [255, 0, 0, 200]: return "Red"
    return "Unknown"

subs_display['viability'] = subs_display['color'].apply(_get_viability)
viability_counts = subs_display['viability'].value_counts().to_dict()

# ── Layer 1 – Substations ──────────────────────────────────────────────────────
if show_subs:
    map_layers.append(pdk.Layer(
        "ScatterplotLayer", subs_display,
        id="substations",
        get_position="[lon, lat]",
        get_color="color",
        get_radius=600,
        pickable=True,
        auto_highlight=True,
    ))

# ── Layers 2-N – Generation Sources (one layer per selected category) ──────────
if show_gen and gen_filtered is not None:
    for cat in GENERATION_CATEGORIES:
        if cat not in selected_categories:
            continue
        cat_df = gen_filtered[gen_filtered['category'] == cat].copy()
        if cat_df.empty:
            continue
        rgba = GENERATION_CATEGORY_COLORS[cat]
        map_layers.append(pdk.Layer(
            "ScatterplotLayer", cat_df,
            id=f"gen_{cat.lower()}",
            get_position="[lon, lat]",
            get_color=rgba,          # constant colour – all rows in this layer share it
            get_radius=2500,
            pickable=True,
            auto_highlight=True,
        ))

# ── Layer – Existing Data Centres ─────────────────────────────────────────────
if show_dc and dc_filtered is not None:
    map_layers.append(pdk.Layer(
        "ColumnLayer", dc_filtered,
        id="data-centres",
        get_position="[lon, lat]",
        get_elevation="load_mw * 10",
        elevation_scale=1,
        get_fill_color=[200, 30, 30, 150],
        radius=800,
        pickable=True,
    ))

# ── Layer – Estimated EV charger demand by substation region ──────────────────
if show_ev:
    map_layers.append(pdk.Layer(
        "ColumnLayer", subs_display,
        id="ev-demand",
        get_position="[lon, lat]",
        get_elevation="ev_load_mw * 10",
        elevation_scale=1,
        get_fill_color=[255, 215, 0, 150],
        radius=700,
        pickable=True,
        auto_highlight=True,
    ))

# ── Layer – Proposed DC Site ───────────────────────────────────────────────────
proposed_dc_loc = pd.DataFrame([{
    'name': 'Proposed DC Site',
    'lat':  sub_info['lat'] + 0.01,
    'lon':  sub_info['lon'] + 0.01,
    'load_mw': dc_load,
}])
map_layers.append(pdk.Layer(
    "ScatterplotLayer", proposed_dc_loc,
    id="proposed-dc",
    get_position="[lon, lat]",
    get_color=[0, 255, 100, 255],
    get_radius=1200,
))

# ── Layer – Network Flow Arcs ─────────────────────────────────────────────────
if show_flow and gen_filtered is not None:
    # Only draw arcs from visible categories
    visible_gen = (
        gen_filtered[gen_filtered['category'].isin(selected_categories)]
        if selected_categories else gen_filtered
    )
    flow_lines = [
        {'start': [g.lon, g.lat], 'end': [sub_info.lon, sub_info.lat]}
        for _, g in visible_gen.iterrows()
    ]
    if flow_lines:
        map_layers.append(pdk.Layer(
            "ArcLayer", pd.DataFrame(flow_lines),
            id="flow-arcs",
            get_source_position="start",
            get_target_position="end",
            get_source_color=[255, 200, 0, 80],
            get_target_color=[0,   200, 255, 80],
            width_scale=2,
            width_min_pixels=1,
        ))

# ══════════════════════════════════════════════════════════════════════════════
# RENDER MAP
# ══════════════════════════════════════════════════════════════════════════════
tooltip = {
    "html": (
        "<b>{name}</b><br/>"
        "Fuel: {fuel_type} &nbsp;|&nbsp; Category: {category}<br/>"
        "Capacity: {capacity_mw} MW<br/>"
        "Region: {region}<br/>"
        "Status: {status}<br/>"
        "Substation Headroom: {headroom_mw} MW"
    ),
    "style": {
        "backgroundColor": "#0d1b2a",
        "color": "#e0f0ff",
        "maxWidth": "320px",
        "fontSize": "13px",
        "lineHeight": "1.6",
        "padding": "10px 14px",
        "borderRadius": "6px",
        "boxShadow": "0 4px 12px rgba(0,0,0,0.5)",
    },
}

st.pydeck_chart(pdk.Deck(
    map_style=_THEME_MAP[map_theme],
    initial_view_state=pdk.ViewState(
        latitude=sub_info['lat'], longitude=sub_info['lon'],
        zoom=7, pitch=40,
    ),
    layers=map_layers,
    tooltip=tooltip,
))

# ══════════════════════════════════════════════════════════════════════════════
# ANALYSIS COLUMNS
# ══════════════════════════════════════════════════════════════════════════════
col_node, col_legend = st.columns([1, 1])

with col_node:
    st.markdown("#### 🔌 Node Analysis")
    st.markdown(f"**Target Node:** `{target_sub}`")
    st.metric("Net Headroom (MW)", f"{remaining_headroom:.2f}", delta=-total_new_load_mw)
    st.markdown(f"**EV Load (Estimated + Simulated):** `{effective_ev_load_mw:.2f} MW`")
    st.markdown(f"**Reliability Probability:** `{reliability:.2f}%`")
    st.markdown(f"**Status:** `{status}` — *{color_text}*")
    st.markdown("---")
    if status == "HIGH RISK":
        st.error("**Recommendation:** Transformer Upgrade Required for 2026 Capacity.")
    elif status == "FEASIBLE":
        st.warning("**Recommendation:** Viable, but grid stress observed. Requires IESO connection assessment.")
    else:
        st.success("**Recommendation:** Grid Node appears highly viable for development.")

with col_legend:
    with st.expander("🗺️ Map Legend", expanded=True):
        st.markdown(f"""
**Substations**
- 🟢 **Green** — Highly Viable (**{viability_counts.get('Green', 0)}**)
- 🟠 **Orange** — Feasible (**{viability_counts.get('Orange', 0)}**)
- 🔴 **Red** — High Risk (**{viability_counts.get('Red', 0)}**)

**Generation Sources** *(by category)*
- 🟣 **Purple** — Nuclear
- 🔵 **Blue** — Hydro
- 🟠 **Orange-Red** — Fossil (Natural Gas)
- 🟢 **Green** — Renewable (Wind / Solar / Biofuel)
- 🟤 **Violet** — Battery Storage

**Other**
- 🔴 **Dark Red Column** — Existing Data Centres
- 🟢 **Bright Dot** — Proposed DC Site
- 🟡〰️🔵 **Arc Lines** — Network Flow
        """)

# ── Generation Source Summary Table ───────────────────────────────────────────
st.markdown("---")
st.markdown("#### 📊 Ontario Generation Fleet Summary *(IESO data)*")

if gen_filtered is not None:
    # Filter to currently selected categories for summary
    _display_gen = (
        gen_filtered[gen_filtered['category'].isin(selected_categories)]
        if selected_categories else gen_filtered
    )
    summary = (
        _display_gen
        .groupby(['category', 'fuel_type'])
        .agg(
            Plants=('name', 'count'),
            Total_MW=('capacity_mw', 'sum'),
        )
        .reset_index()
        .rename(columns={'category': 'Category', 'fuel_type': 'Fuel Type',
                         'Total_MW': 'Total Capacity (MW)'})
        .sort_values(['Category', 'Fuel Type'])
    )
    summary['Total Capacity (MW)'] = summary['Total Capacity (MW)'].map('{:,.0f}'.format)
    st.dataframe(summary, use_container_width=True, hide_index=True)

    # Grand total badge
    total_mw = _display_gen['capacity_mw'].sum()
    st.caption(
        f"**Shown:** {len(_display_gen)} facilities · "
        f"**Total Visible Capacity:** {total_mw:,.0f} MW"
    )
else:
    st.info("Generation source data not available.")

st.markdown("---")
st.caption(
    f"**Technical Note:** Calculations incorporate a 1.15 Safety Factor and "
    f"I²R Estimated Heat Loss of **{losses:.4f} MW**, alongside a Monte Carlo "
    f"simulation using a Triangular Distribution (40% min, 70% typical, 100% peak ambient load). "
    f"EV charging demand is approximated by regional population and distributed across substations "
    f"for scenario planning (demo assumption). "
    f"Generation data sourced from IESO Reliability Outlook (Dec 2025) & IESO Year-End Data 2025."
)
