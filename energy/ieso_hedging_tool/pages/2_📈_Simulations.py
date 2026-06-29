# pages/2_📈_Simulations.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from energy.ieso_hedging_tool.src.finance.models import EnergySimulator
from energy.ieso_hedging_tool.src.finance.finance import calculate_ga_cost, calculate_energy_greeks

st.title("📈 Monte Carlo Risk Simulation")
st.markdown("---")

# 2. Persistent Data Logic
if 'market_data' in st.session_state:
    data = st.session_state['market_data']
    st.success(f"✅ Loaded Market Data. Using historical mean for simulation.")
    default_mu = float(data['Ontario Price'].mean())
    default_s0 = float(data['Ontario Price'].iloc[-1]) # Start from the last known price
else:
    st.warning("⚠️ No market data loaded. Using default simulation parameters.")
    default_mu = 35.0
    default_s0 = 40.0

# 3. User Inputs
with st.sidebar:
    st.markdown("**OU Model Parameters**")
    mu = st.number_input("Long-term Mean (μ)", value=default_mu)
    theta = st.slider("Reversion Speed (θ)", 0.05, 0.5, 0.15)
    sigma = st.slider("Volatility (σ)", 0.1, 10.0, 2.5)
    
    st.markdown("**Hedge Settings (for P&L tracking)**")
    strike = st.number_input("Hedge Strike ($)", value=45.0)
    iv = st.slider("Implied Volatility (%)", 20, 150, 80) / 100

# 4. Simulation Engine
if st.button("Run Simulation Engine"):
    sim = EnergySimulator(s0=default_s0, mu=mu, theta=theta, sigma=sigma)
    n_paths = 100  # Number of iterations
    n_hours = 720  # 1 Month
    
    all_paths = []
    unhedged_costs = []
    hedged_costs = []

    for i in range(n_paths):
        path = sim.run_monte_carlo(n_steps=n_hours)
        all_paths.append(path)
        
        # Calculate Unhedged Cost
        unhedged_cost = np.sum(path * 5) # 5MW load
        
        # --- CALCULATE HEDGED COST (Dynamic P&L Tracking) ---
        # Payoff = Max(Price - Strike, 0). 
        # We assume the "Cap" pays out at the end of the month based on hourly spikes.
        payoffs = np.maximum(path - strike, 0)
        total_payoff = np.sum(payoffs * 5)
        
        # All-in Cost = (Market Spend - Hedge Payoff) + GA
        ga_cost = 5 * 720 * 0.06 # Placeholder GA Class B
        hedged_costs.append(unhedged_cost - total_payoff + ga_cost)
        unhedged_costs.append(unhedged_cost + ga_cost)

    # --- VISUALIZATION: Price Paths ---
    st.subheader("Simulated Hourly Price Paths")
    fig = go.Figure()
    for i in range(min(n_paths, 20)): # Plot first 20 paths
        fig.add_trace(go.Scatter(y=all_paths[i], mode='lines', line=dict(width=0.5), opacity=0.3, showlegend=False))
    fig.add_trace(go.Scatter(y=np.mean(all_paths, axis=0), name="Average Path", line=dict(color='red', width=3)))
    st.plotly_chart(fig, use_container_width=True)

    # --- VISUALIZATION: Cost Distribution ---
    st.subheader("Budget Risk: Hedged vs. Unhedged")
    df_dist = pd.DataFrame({
        'Unhedged': unhedged_costs,
        'Hedged (Cap)': hedged_costs
    })
    
    # We use a histogram to show how the "Hedged" version has a lower 'Tail Risk'
    import plotly.express as px
    fig_hist = px.histogram(df_dist, barmode='overlay', nbins=30)
    st.plotly_chart(fig_hist, use_container_width=True)
    
    st.info("""
    **Insight for Clients:** Notice how the 'Hedged' distribution (blue/green) is shifted to the left and is 'tighter'. 
    This shows that while you pay a premium, you've eliminated the extreme 'Black Swan' spikes on the right side of the graph.
    """)
