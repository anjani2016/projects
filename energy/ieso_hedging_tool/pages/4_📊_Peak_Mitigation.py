# pages/4_📊_Peak_Mitigation.py
import datetime
import numpy as np
import pandas as pd
import streamlit as st
from energy.ieso_hedging_tool.src.finance.peak_engine import PeakMitigationEngine

st.set_page_config(page_title="H-PHA Pilot Module", layout="wide")

st.title("Class A Historical Peak Hour Analysis (H-PHA)")
st.caption("Phase 1 Pilot Engine — Global Adjustment Mitigation Simulator")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("1. Client Asset Configuration")
curtailment = st.sidebar.slider(
    "Available Curtailment (kW)",
    min_value=0,
    max_value=2000,
    value=500,
    step=50,
)

st.sidebar.markdown("---")
st.sidebar.header("2. Battery Storage (BESS)")
battery_power = st.sidebar.slider(
    "Battery Power Rating (kW)", min_value=0, max_value=2000, value=250, step=50
)
battery_capacity = st.sidebar.slider(
    "Battery Capacity (kWh)", min_value=0, max_value=4000, value=500, step=100
)
efficiency = st.sidebar.slider(
    "Round-Trip Efficiency (%)", min_value=70, max_value=98, value=88, step=1
)

st.sidebar.markdown("---")
st.sidebar.header("3. Financial Assumptions")
ga_pool = st.sidebar.number_input(
    "Est. Ontario Class A GA Pool ($)", value=3_100_000_000, step=50_000_000
)

# --- MOCK DATA GENERATOR (For Pilot Demonstration) ---
# In production, this would read from your database or an uploaded CSV
timestamps = [
    datetime.datetime(2025, 7, 15, 17, 0),
    datetime.datetime(2025, 7, 16, 16, 0),
    datetime.datetime(2025, 8, 3, 17, 0),
    datetime.datetime(2025, 8, 21, 18, 0),
    datetime.datetime(2025, 9, 4, 16, 0),
]


@st.cache_data
def get_mock_ieso_data():
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "ieso_system_mw": [22450, 23110, 21980, 22640, 23400],
            "peak_rank": [3, 2, 5, 4, 1],
        }
    )


@st.cache_data
def get_mock_client_data():
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "client_kw": [4500, 4720, 4410, 4600, 4850],
        }
    )


# Run Engine
engine = PeakMitigationEngine(total_ga_pool=ga_pool)
df_ieso = get_mock_ieso_data()
df_client = get_mock_client_data()

sim_results = engine.simulate_mitigation(
    df_client=df_client,
    df_ieso_peaks=df_ieso,
    curtailment_kw=curtailment,
    battery_kw=battery_power,
    battery_kwh=battery_capacity,
    battery_eff=efficiency / 100.0,
)

summary = sim_results["summary"]
breakdown = sim_results["event_breakdown"]

# --- MAIN DASHBOARD DISPLAY ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="Simulated GA Savings", value=f"${summary['total_savings']:,.2f}"
    )
with col2:
    reduction = summary["original_ga_cost"] - summary["mitigated_ga_cost"]
    st.metric(
        label="New GA Obligation",
        value=f"${summary['mitigated_ga_cost']:,.2f}",
        delta=f"-${reduction:,.2f}",
        delta_color="inverse",
    )
with col3:
    st.metric(
        label="Avg Peak Reduction",
        value=f"{summary['net_peak_reduction_kw']:.1f} kW",
    )

st.markdown("---")
st.subheader("Coincident Peak Event Analysis")
st.caption(
    "The 5 hours that determined your client's Global Adjustment allocation for the billing year:"
)

# Display scannable results table
display_df = breakdown.copy()
display_df["timestamp"] = display_df["timestamp"].dt.strftime(
    "%Y-%m-%d %H:%M"
)
st.dataframe(
    display_df.style.format(
        {
            "ieso_system_mw": "{:,.0f} MW",
            "original_kw": "{:,.1f} kW",
            "mitigated_kw": "{:,.1f} kW",
            "curtailment_reduction_kw": "{:,.1f} kW",
            "battery_reduction_kw": "{:,.1f} kW",
            "orig_pf": "{:.7f}",
            "mitigated_pf": "{:.7f}",
        }
    ),
    hide_index=True,
    use_container_width=True,
)

# Render Chart Comparison
st.markdown("---")
st.subheader("Demand Reduction Profile Across Top 5 Peaks")
chart_data = pd.DataFrame(
    {
        "Original Demand (kW)": breakdown["original_kw"].values,
        "Mitigated Demand (kW)": breakdown["mitigated_kw"].values,
    },
    index=[f"Peak {r}" for r in breakdown["peak_rank"]],
)
st.bar_chart(chart_data)