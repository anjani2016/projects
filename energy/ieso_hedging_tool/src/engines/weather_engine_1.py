# engines/weather_engine.py
import datetime
import requests
import pandas as pd
import streamlit as st

@st.cache_data(ttl=3600)  # Cache weather telemetry for 1 hour
def fetch_live_gta_weather(days_back: int = 14) -> pd.DataFrame:
    """
    Queries actual hourly ambient temperatures for the Greater Toronto Area.
    Coordinates default near the Mississauga/Toronto data center cluster (43.65, -79.61).
    """
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=days_back)
    
    # Constructing parameters for the Open-Meteo telemetry endpoint
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude=43.65&longitude=-79.61"
        f"&start_date={start_date}&end_date={today}"
        f"&hourly=temperature_2m"
        f"&timezone=America%2FNew_York"
    )
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        hourly_data = response.json().get("hourly", {})
        
        df_weather = pd.DataFrame({
            "Timestamp": pd.to_datetime(hourly_data.get("time")),
            "Temperature (°C)": hourly_data.get("temperature_2m")
        })
        return df_weather
    except Exception as e:
        st.error(f"Weather Telemetry Pipeline Error: {e}")
        return pd.DataFrame()