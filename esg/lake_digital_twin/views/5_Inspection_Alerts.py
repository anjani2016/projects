import streamlit as st
import numpy as np
from models.inspection_engine import evaluate_inspection_triggers, generate_ai_brief

st.title("🚨 Autonomous Inspection Alerts")
st.write("This dashboard monitors weather patterns, satellite observations, and volunteer field reports in real time to automatically request human verification when water quality thresholds are crossed.")

# --- SIDEBAR: Live Simulation Controls ---
st.sidebar.subheader("🎛️ Simulation Controls")
st.sidebar.write("Simulate environmental inputs to test alert triggers:")

sim_rain = st.sidebar.slider("Forecasted 24h Rain (mm)", 0, 150, 20, help="Heavy rain triggers runoff model alerts.")
sim_air_temp = st.sidebar.slider("Forecasted Air Temp (°C)", 10, 40, 25)
sim_gradient = st.sidebar.slider("Volunteer Temp Delta (Surface - 1m) (°C)", 0.0, 5.0, 0.8, step=0.1, help="Difference in water temperature indicates stratification.")
sim_secchi = st.sidebar.slider("Volunteer Secchi Depth (m)", 0.5, 10.0, 3.2, step=0.1)
sim_sat = st.sidebar.checkbox("Satellite NDCI Anomaly Detected", value=False, help="Simulate a satellite spectral anomaly spike (chlorophyll/algae).")

st.sidebar.markdown("---")
st.sidebar.subheader("🔑 Gemini API Configuration")
api_key = st.sidebar.text_input("Gemini API Key (Optional)", type="password", help="If provided, Gemini will write a custom dispatch brief. If empty, the system uses a local template.")

# Default coordinates for York Region/Ontario lakes
lat = 44.00
lon = -79.47

selected_lake = st.session_state.get("selected_lake")
if selected_lake:
    st.info(f"📍 **Lake Context Active:** {selected_lake['name']} | Coordinates: {lat}, {lon}")
else:
    st.warning("No lake selected. Simulating with default coordinates (York Region, ON).")

# --- RULES EVALUATION ---
is_triggered, risk_score, active_alerts = evaluate_inspection_triggers(
    weather_rain=sim_rain,
    weather_forecast_temp=sim_air_temp,
    volunteer_gradient=sim_gradient,
    volunteer_secchi=sim_secchi,
    sat_anomaly_detected=sim_sat,
    lat=lat,
    lon=lon
)

# --- DISPLAY ALERTS ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("System Status")
    
    if is_triggered:
        st.error("🔴 INSPECTION DISPATCH REQUIRED")
        st.metric("Composite Risk Index", f"{risk_score}/100", delta="THRESHOLD EXCEEDED", delta_color="inverse")
    else:
        st.success("🟢 NORMAL MONITORING STATE")
        st.metric("Composite Risk Index", f"{risk_score}/100", delta="SECURE")
        
    st.markdown("---")
    st.write("**Active Alert Flags:**")
    if active_alerts:
        for alert in active_alerts:
            st.warning(f"⚠️ {alert}")
    else:
        st.info("No warning thresholds breached.")

with col2:
    st.subheader("Field Dispatch Center")
    if is_triggered:
        st.write("An automated dispatch brief has been generated for regional coordinators to deploy field sampling kits.")
        
        # Load or generate brief
        with st.spinner("Generating field brief..."):
            brief = generate_ai_brief(api_key, risk_score, active_alerts, (lat, lon))
            
        st.info(brief)
        
        # Action button
        if st.button("🚀 Send Alerts to Local Volunteer Network"):
            st.success("Notification sent! Field inspection requested at simulated coordinates.")
    else:
        st.write("All parameters are within normal ecological bounds. No manual inspection is currently required.")
        st.info("💡 **Try simulating higher temperatures, more rain, or checking the satellite anomaly box in the sidebar to trigger an inspection.**")
