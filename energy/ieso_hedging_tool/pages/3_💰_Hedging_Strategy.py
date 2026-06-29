# pages/3_💰_Hedging_Strategy.py
import streamlit as st
import pandas as pd
from energy.ieso_hedging_tool.src.finance.finance import calculate_energy_greeks, calculate_advanced_greeks, calculate_ga_cost

st.title("💰 Hedging Strategy Engine")
st.markdown("---")

st.info("This module calculates option premiums and Greeks based on the Black-Scholes model tailored for energy markets.")

# 1. Check for Persistent Data
if 'market_data' in st.session_state:
    data = st.session_state['market_data']
    st.success(f"✅ Loaded Market Data for {st.session_state.get('selected_month', 'selected month')}")
    avg_price = data['Ontario Price'].mean()
else:
    st.warning("⚠️ No market data loaded. Using default spot price for calculation.")
    avg_price = 40.0

col1, col2 = st.columns(2)

with col1:
    st.subheader("Strategy Parameters")
    spot_price = st.number_input("Current Spot Price ($/MWh)", value=float(avg_price))
    strike_price = st.number_input("Strike Price ($/MWh)", value=45.0)
    contract_volume = st.number_input("Monthly Volume (MWh)", value=1000)
    days_to_expiry = st.slider("Days to Expiry", 1, 365, 30)

with col2:
    st.subheader("Market Inputs")
    risk_free_rate = st.slider("Risk-Free Rate (%)", 0.0, 10.0, 4.5) / 100
    implied_vol = st.slider("Implied Volatility (%)", 10, 200, 80) / 100
    ga_class = st.selectbox("Consumer Class (GA)", ["B", "A"])
    pdf = st.number_input("Peak Demand Factor (Class A only)", value=0.0005, format="%.6f") if ga_class == "A" else 0.0

if st.button("Calculate Hedge Premium & Greeks"):
    T = days_to_expiry / 365
    greeks = calculate_advanced_greeks(spot_price, strike_price, T, risk_free_rate, implied_vol)
    ga_cost = calculate_ga_cost(contract_volume, ga_class, pdf)
    
    st.markdown("---")
    st.subheader("Results")
    
    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric("Option Premium", f"${greeks['Premium']:.2f}")
    res_col2.metric("Total Premium Cost", f"${(greeks['Premium'] * contract_volume):,.2f}")
    res_col3.metric("Est. GA Cost", f"${ga_cost:,.2f}")
    
    st.markdown("### Risk Greeks")
    g_col1, g_col2, g_col3, g_col4 = st.columns(4)
    g_col1.metric("Delta", greeks['Delta'])
    g_col2.metric("Gamma", greeks['Gamma'])
    g_col3.metric("Vega", greeks['Vega'])
    g_col4.metric("Theta", greeks['Theta'])
    
    st.info(f"**Insight:** A Delta of {greeks['Delta']} means for every $1 increase in spot price, your hedge value increases by ${greeks['Delta'] * contract_volume:,.2f}.")

st.markdown("---")
