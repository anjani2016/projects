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
from energy.ontario_grid_twin.src.engine.data_loader import load_base_grid, load_dc_projects, get_grid_nodes
from energy.ontario_grid_twin.src.utils.ui_branding import apply_branding
import pandas as pd
# 1. Page Configuration
st.set_page_config(
    page_title="Ontario Grid Digital Twin",
    page_icon="⚡",
    layout="wide"
)

# 2. Global branding
apply_branding()

# 3. Global Data Initialization (Loaded into Session State for cross-page access)
if 'data_loaded' not in st.session_state:
    with st.spinner("Initializing Digital Twin Engine..."):
        subs, lines, gen, dc = load_base_grid()
        projects, provincial_interest_mw, dc_source = load_dc_projects()
        grid_nodes = get_grid_nodes(subs)
        
        st.session_state['subs'] = subs
        st.session_state['lines'] = lines
        st.session_state['gen'] = gen
        st.session_state['dc'] = dc
        st.session_state['projects'] = projects
        st.session_state['provincial_interest_mw'] = provincial_interest_mw
        st.session_state['dc_source'] = dc_source
        st.session_state['grid_nodes'] = grid_nodes
        st.session_state['data_loaded'] = True

# 4. Landing Page: Home
st.title("⚡ Ontario Grid Digital Twin")
st.subheader("Interactive planning workspace for substation reliability and large step load assessment")

st.markdown("""
Use this dashboard to evaluate where large new loads are most feasible by combining:
- substation headroom and probabilistic reliability modeling
- generation-source visibility and regional filtering
- project portfolio views for planned data-centre demand

Navigate from the sidebar to:
- **Project Charter** for methodology, assumptions, and source references
- **Grid Centres** for infrastructure classification and regional tracking
- **Data Centres** for existing and projected Datacentre projects outlook
- **Node Analysis** for node-level simulation and map overlays
- **Grid Reliability Analysis** for probabilistic distribution analysis

""")

st.divider()


col1, col2 = st.columns(2)
with col1:
    st.markdown("### 🛠️ Technical Stack")
    st.write("- **Language:** Python 3.11")
    st.write("- **App Framework:** Streamlit multi-page architecture")
    st.write("- **Data + Analytics:** Pandas, NumPy")
    st.write("- **Geospatial:** GeoPandas, Shapely, PyDeck")
    st.write("- **Storage:** Parquet/GeoParquet")
    st.write("- **Data Ingestion:** IESO public XML feeds + local curated datasets")
    
with col2:
    st.markdown("### 📊 Methodology")
    st.write("- **Probabilistic Reliability:** Monte Carlo simulation with triangular load profile")
    st.write("- **Electrical Stress Proxy:** I²R-based loss estimation for incremental load impact")
    st.write("- **Headroom Logic:** Capacity minus safety-adjusted base load")
    st.write("- **Cooling Context:** Non-linear free-cooling efficiency with 8% floor")
    st.write("- **Regional Planning Lens:** Linked substation + generation filtering by region")

st.divider()

st.markdown("### 🔍 Verified Data Sources (Updated May 2026)")
sources_data = {
    "Category": [
        "Substation & Transmission",
        "Generation Fleet Layer",
        "Data Centre Pipeline",
        "Regional Demand Outlook",
        "Macro Energy Futures",
        "Planning Methodology",
        "Consumption Context",
        "Climate Context",
        ],
    "Source": [
        "IESO Public Reports",
        "IESO Market Data",
        "Baxtel + Nat. Observer",
        "IESO 2026 APO",
        "CER Energy Future 2026",
        "IESO Technical Paper",
        "StatCan",
        "Open-Meteo API",
        ],
    "Details / Primary Links": [
        "[Tx Interface Outage Limits (XML)](http://reports.ieso.ca/public/TxInterfaceLimits/)",
        "[Generator Output by Fuel Type (Live Data)](https://www.ieso.ca/power-data)",
        "[Baxtel Map](https://baxtel.com/map) | [Nat. Observer DC Mapping](https://www.nationalobserver.com/)",
        "[2026 Annual Planning Outlook (Summary & Data)](https://www.ieso.ca/en/sector-participants/planning-and-forecasting/annual-planning-outlook)",
        "[CER: Exploring Canada's Energy Future 2026](https://www.cer-rec.gc.ca/en/data-analysis/canada-energy-future/index.html)",
        "[Large Step Loads Technical Paper (July 2025)](https://www.ieso.ca/-/media/Files/IESO/Document-Library/planning-forecasts/demand-research/Demand-Conservation-Planning-Technical-Paper-Large-Step-Loads-202507.pdf)",
        "[Canadian Economic & Energy Dashboard (71-607-X)](https://www150.statcan.gc.ca/n1/pub/71-607-x/71-607-x2021004-eng.htm)",
        "[Historical & Real-Time Weather Data](https://open-meteo.com/)",
        ]
    }
    
    # Render sources as a markdown table to support links better than st.table
df_sources = pd.DataFrame(sources_data)
st.markdown(df_sources.to_markdown(index=False))

st.divider()


st.info("💡 **Getting Started:** Open `Interactive Grid Map`, select a region and target substation, then tune simulated load to compare reliability outcomes.")

st.caption("Developed by: Centauri Research / Advanced Grid Engineering")
st.caption("Reference Date: May 2026")
