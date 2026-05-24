import streamlit as st
import folium
import time
import random
from streamlit_folium import st_folium
from folium.features import DivIcon
from src.utils.harvester import AISHarvester

st.set_page_config(page_title="Hormuz Tactical Monitor", layout="wide")
harvester = AISHarvester()

# State initialization
if 'refresh_seq' not in st.session_state:
    st.session_state.refresh_seq = [2, 5]
if 'next_refresh_time' not in st.session_state:
    st.session_state.next_refresh_time = time.time()
if 'mock_df' not in st.session_state:
    st.session_state.mock_df = None

now = time.time()
if now >= st.session_state.next_refresh_time or st.session_state.mock_df is None:
    # Fetch new data
    st.session_state.mock_df = harvester.fetch_live_data()
    
    # Calculate next interval
    if len(st.session_state.refresh_seq) > 0:
        interval = st.session_state.refresh_seq.pop(0)
    else:
        interval = random.choice([2, 5, 10, 12, 20])
    
    st.session_state.next_refresh_time = time.time() + interval
st.sidebar.header("Settings")
predict_min = st.sidebar.slider("Prediction Window (Min)", 5, 60, 15)
safety_km = st.sidebar.slider("Safety Buffer (KM)", 0.1, 2.0, 0.5)

# Pipeline
df = st.session_state.mock_df
df = harvester.process_data(df)
df = harvester.predict_future_positions(df, minutes_ahead=predict_min)
risks = harvester.detect_collisions(df, safety_radius_km=safety_km)

st.title("🚢 Hormuz Tactical Monitor")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Phase 1: API Ingestion",
    "Phase 2: Mock Data",
    "Phase 3: Processing",
    "Phase 4: Risk Tagging",
    "Phase 5: Predictive Paths",
    "Phase 6: Collision Warning"
])

with tab1:
    st.header("Phase 1: Live API Ingestion")
    st.write("Fetching live vessel data from the AIS API...")
    st.dataframe(st.session_state.mock_df, use_container_width=True)

with tab2:
    st.header("Phase 2: Mock Data Generator")
    st.write("If the API is unavailable, the system gracefully falls back to generating realistic mock data.")
    st.code("vessel_data = harvester._generate_mock_data()")

with tab3:
    st.header("Phase 3: Data Normalization & Processing")
    st.write("Standardizing column names and ensuring mandatory UI columns exist.")
    st.dataframe(df.drop(columns=['pred_lat', 'pred_lon', 'path', 'stale_minutes', 'is_dark', 'in_critical_zone'], errors='ignore'), use_container_width=True)

with tab4:
    st.header("Phase 4: Geospatial Risk Tagging")
    st.write("Identifying dark ships (stale signals) and vessels entering critical geopolitical zones.")
    st.dataframe(df[['mmsi', 'timestamp', 'stale_minutes', 'is_dark', 'in_critical_zone']], use_container_width=True)

with tab5:
    st.header("Phase 5: Predictive Engine")
    st.write(f"Calculating projected positions {predict_min} minutes ahead based on current course and speed.")
    st.dataframe(df[['mmsi', 'lat', 'lon', 'course', 'speed', 'pred_lat', 'pred_lon']], use_container_width=True)

with tab6:
    st.header("Phase 6: Collision Warning System")
    m = folium.Map(location=[26.7, 56.3], zoom_start=8, tiles="CartoDB dark_matter")
    
    # Draw Collisions first (so they are under markers)
for risk in risks:
    folium.PolyLine(locations=[risk['pos_a'], risk['pos_b']], color="red", weight=5).add_to(m)

    for _, row in df.iterrows():
        color = "#FF0000" if row['is_dark'] else ("#FFA500" if row['in_critical_zone'] else "#00BFFF")
        icon_html = f'<div style="transform: rotate({row["course"]}deg); color: {color}; font-size: 20px;">➤</div>'
        folium.Marker(location=[row['lat'], row['lon']], icon=DivIcon(html=icon_html)).add_to(m)
        
        # Ghost Path
        folium.PolyLine(locations=[(row['lat'], row['lon']), (row['pred_lat'], row['pred_lon'])], 
                        color="white", weight=1, dash_array='5, 5', opacity=0.4).add_to(m)

    st_folium(m, width=1200, height=600)

    if risks:
        st.error(f"🚨 {len(risks)} Collision Risks Detected")
        st.table(risks)

# Auto-refresh logic
remaining_time = st.session_state.next_refresh_time - time.time()
if remaining_time > 0:
    time.sleep(remaining_time)
st.rerun()