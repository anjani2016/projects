import streamlit as st
import os

# --- Title Section ---
st.title("🌊 Lake Health Digital Twin: Strategic Overview")
st.markdown("""
**An Engineering-Grade Framework for Predictive Water Management**  
*Lead Engineer: Anjani Duddukuru, P.Eng, PMP, PMI-RMP*
---
""")

# --- Project Objectives ---
st.header("🎯 Project Objectives")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("1. Predictive Modeling")
    st.write("""
    - Simulate nutrient flux (Phosphorus/Nitrogen) based on high-resolution rainfall events.
    - Forecast Trophic State changes to provide early warnings for harmful algae blooms.
    """)

with col2:
    st.subheader("2. Decision Support")
    st.write("""
    - Provide a 'Virtual Jar Test' environment for chemical treatment validation before deployment.
    - Optimize municipal and agricultural planning through lakeshore capacity assessment.
    """)

with col3:
    st.subheader("3. Automated Inspection")
    st.write("""
    - Perform continuous auto-checks on weather forecasts, volunteer field data, and satellite inputs.
    - Automatically trigger human-in-the-loop inspections and AI-generated field briefs.
    """)

# --- The Technical Approach ---
st.header("🔄 Operational Workflow")
st.info("**Methodology:** A continuous early-warning loop combining physical simulation, satellite remote sensing, and citizen science validation.")

# Visual Status Legend
col_leg_a, col_leg_b, col_leg_f = st.columns(3)
col_leg_a.markdown("🔵 **[ACTUAL]** — Implemented production-grade baseline data or math.")
col_leg_b.markdown("🟡 **[SIMULATED]** — Mocked/generated for frontend verification.")
col_leg_f.markdown("🟣 **[FUTURE WORK]** — Slated for cloud/API migration roadmap.")

st.markdown("### Operational Workflow Status")

# Render columns natively for Streamlit
col1, col2, col3, col4 = st.columns(4)

with col1:
    with st.container(border=True):
        st.markdown("#### 📡 1. Baseline Ingestion")
        st.caption("🔵 **Lake Metadata** (ACTUAL)")
        st.caption("🟡 **3D Bathymetry** (SIMULATED)")
        st.caption("🟣 **Sentinel-2 Bands** (FUTURE)")

with col2:
    with st.container(border=True):
        st.markdown("#### 🌤️ 2. Weather Scenarios")
        st.caption("🔵 **Stumm-Morgan Math** (ACTUAL)")
        st.caption("🟡 **Forecast Sliders** (SIMULATED)")
        st.caption("🟣 **MSC Weather API** (FUTURE)")

with col3:
    with st.container(border=True):
        st.markdown("#### 📍 3. Volunteer Ground-Truth")
        st.caption("🔵 **Secchi & Temp Inputs** (ACTUAL)")
        st.caption("🟣 **Live DataStream API** (FUTURE)")
        st.markdown("<br>", unsafe_allow_html=True) # visual spacer

with col4:
    with st.container(border=True):
        st.markdown("#### 🚨 4. Alert & Dispatch")
        st.caption("🔵 **Rule Checks** (ACTUAL)")
        st.caption("🔵 **Gemini AI Briefs** (ACTUAL)")
        st.caption("🔵 **Dispatch Cards UI** (ACTUAL)")


flow_baseline, flow_simulation, flow_calibration, flow_action = st.tabs([
    "1. Baseline Monitoring", 
    "2. Weather Scenario Simulation", 
    "3. Volunteer Validation", 
    "4. Alert & Action Dispatch"
])

with flow_baseline:
    st.markdown("""
    ### 📡 Baseline Ingestion
    The system begins by establishing a high-resolution spatial and structural foundation for each water body:
    * **Bathymetry Mesh:** Building 3D volumetric models to track storage capacity and hypoxic zones.
    * **Satellite Remote Sensing:** Continuous ingestion of Sentinel-2 L2A multispectral bands:
      * **NDWI / MNDWI:** Masks water bodies to isolate open water surface.
        $$NDWI = \\frac{\\text{Green} - \\text{NIR}}{\\text{Green} + \\text{NIR}}$$
      * **NDCI (Chlorophyll Proxy):** Spots surface algae activity.
        $$NDCI = \\frac{\\text{RedEdge1} - \\text{Red}}{\\text{RedEdge1} + \\text{Red}}$$
      * **NDTI (Turbidity Proxy):** Maps suspended sediment concentration.
        $$NDTI = \\frac{\\text{Red} - \\text{Green}}{\\text{Red} + \\text{Green}}$$
    """)

with flow_simulation:
    st.markdown("""
    ### 🌤️ Weather Forecast & Scenarios
    We use short-range meteorological forecast inputs (precipitation, wind speed, solar radiation) to run predictive models:
    * **Runoff Predictions:** Modeling nutrient loading (Phosphorus/Nitrogen) entering catchment pour-points due to forecasted rainfall.
    * **Stratification Forecasts:** Simulating thermal layers (thermocline formation) using solar radiation and wind forecasts to predict bottom-water hypoxia.
    """)

with flow_calibration:
    st.markdown("""
    ### 📍 Volunteer Ground-Truth
    Citizen science observations from the Lake Partner Program are ingested as an essential calibration source:
    * **Secchi Disk Depths:** Validates and calibrates the satellite-derived turbidity indices.
    * **Temperature Profiles:** Confirms thermocline depth, validating the physical stratification engines.
    """)

with flow_action:
    st.markdown("""
    ### 🚨 Automated Alert & Inspection Dispatch
    When anomalies     * **Alert Logic:** Evaluating combined triggers (Rain $>45\\text{ mm}$, Temp Delta $>1.5^\\circ\\text{C}$, Satellite anomaly spike).
    * **Human-in-the-Loop Inspection:** Generating interactive **Inspection Cards** with target coordinates for regional volunteers.
    * **AI Briefing:** Calling the Gemini API to compile an optimized sampling checklist (e.g. prioritizing deep dissolved oxygen profiling or visual cyanobacteria safety checks).
    """)

st.markdown("---")

st.markdown("# Project Documentation: Ontario Lake Health Digital Twin")
st.write("**Project Stage:** Phase 1 & Phase 2 Integration, with Autonomous Inspection Alerts")
st.write("**Last Updated:** 2026-06-22")

st.markdown("---")

st.subheader("1. Project Vision")
st.write("To develop a predictive 'Living Digital Twin' of Ontario's inland lakes that treats the water body as a biological system (metabolism). The goal is to move from reactive monitoring to predictive intervention using real-time environmental transients and remote sensing.")

st.subheader("2. Core Engineering Logic (Mass Balance)")
st.write("The system operates on the principle of **Accumulation = Input - Output ± Reaction**.")
st.write("- **Inputs:** Rainfall intensity, Agricultural phosphorus loading, and atmospheric deposition.")
st.write("- **Outputs:** Hydraulic flushing (Residence time) and sediment burial.")
st.write("- **Reaction:** Chemical precipitation (Virtual Jar Test) based on the Calcium-to-Phosphorus (Ca:P) ratio.")
st.write("- **Early Warning Triggers:** Rules checking rainfall volume ($>45\\text{ mm}$), temperature stratification gradient ($>1.5^\\circ\\text{C}$), and satellite spectral index anomalies (NDCI chlorophyll spikes) to request human field verification.")

# Include images from assets
col1, col2 = st.columns(2)
with col1:
    st.image(os.path.join(os.path.dirname(__file__), "../data/assets/schematic_lake_digital_twin.png"), caption="Project Schematic: Lake Metabolism Model")
with col2:
    st.image(os.path.join(os.path.dirname(__file__), "../data/assets/chemicalprocess_lake_digital_twin.png"), caption="Chemical Process: Calcium-Phosphorus Reaction")

st.subheader("3. Current Technical Stack")
st.write("- **Framework:** Streamlit (UI/Frontend)")
st.write("- **Environment:** Docker (python:3.11-slim) with `libgomp1` for parallel processing.")
st.write("- **Geospatial Engine:** WhiteboxTools (WBT) for catchment delineation and bathymetry.")
st.write("- **Alerts & AI:** Custom inspection rule checks with integration to Google's Gemini API for dispatch briefs.")
st.write("- **Volunteer Integration:** Coordinates and readings (Secchi Depth, Thermal stratification).")

st.subheader("4. Key Components Developed")
st.write("- **Virtual Jar Test Engine:** A 'What-If' simulator for chemical dosing (Lime/Calcium) to predict phosphorus removal efficiency.")
st.write("- **3D Bathymetry Model:** Dynamic mesh to visualize hypoxia zones and thermocline stratification.")
st.write("- **Autonomous Alert Dashboard:** Real-time trigger evaluation and AI-assisted dispatch card generation.")
st.write("- **Volunteer Mapping Page:** Folium-based coordinate capture to link field readings to specific locations.")

st.subheader("5. Active Transients & Variables")
st.write("- **Clarity/Turbidity:** Measured via Secchi Disk depth and satellite remote sensing.")
st.write("- **Thermal Gradient:** Identifying the thermocline to predict hypolimnetic oxygen depletion.")
st.write("- **Satellite NDCI:** Spotting localized algal growth and suspended sediment anomalies.")

st.subheader("6. Next Milestones")
st.markdown("""
- [x] Establish rule-based early warning thresholds for runoff, stratification, and satellite anomalies.
- [x] Build automated dispatch briefs integrated with the Gemini API.
- [ ] Connect live MSC GeoMet API for real-time weather datasets.
- [ ] Import Lake Partner Program (LPP) historical databases to calibrate remote sensing calculations.
""")

st.markdown("---")
st.info("*This document is a living artifact and is updated as the engineering design evolves.*")

# --- Engineering Standards ---
st.header("⚖️ Standards & Compliance")
st.write("""
This project aligns with the **CCME (Canadian Council of Ministers of the Environment)** guidance for water quality monitoring design and the **Ontario Lakeshore Capacity Assessment** handbook.
""")

# Footer call to action
st.markdown("---")
st.caption("Confidential Project Presentation - Preliminary Engineering Design")