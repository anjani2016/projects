import os
import sys

# Ensure parent directory of 'energy' (grandparent of this file) is in sys.path
# so that imports like `from energy.ieso_hedging_tool.src...` resolve correctly
# both when running locally or deployed on Streamlit Cloud.
current_dir = os.path.dirname(os.path.abspath(__file__))
grandparent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if grandparent_dir not in sys.path:
    sys.path.insert(0, grandparent_dir)

import logging
import streamlit as st
from energy.ieso_hedging_tool.src.core.utils import setup_logger, initialize_project, add_sidebar_branding, add_sidebar_footer
import streamlit.components.v1 as components

# 1. Establish project-wide logging configuration (Streamlit-safe: guarded against duplicate handlers)
setup_logger(log_level=logging.INFO)

# Module-level logger — labelled as 'app' in the log output
logger = logging.getLogger(__name__)
logger.info("IESO Hedging Tool Streamlit app starting up...")

# 2. Setup Page Configuration
st.set_page_config(page_title="IESO Digital Twin", layout="wide")

# Initialize folders and add top-level branding (Contact Info)
initialize_project()
add_sidebar_branding()

# 2. Define the Landing Page (Home)
def show_landing_page():
    st.title("Welcome to the IESO Energy Hedging Tool")
    st.markdown("---")

    # Define Tabs for Overview, Charter, and Value Chain
    tab1, tab2, tab3 = st.tabs(["🏠 Overview & Guide", "📜 Project Charter", "⚡ Energy Value Chain"])

    with tab1:
        st.markdown("""
        ### **Project Purpose**
        This tool acts as a **Financial Digital Twin** for Ontario industrial energy consumers. It allows you to:
        *   **Ingest Data:** Scrape real-time and historical price data from the IESO.
        *   **Simulate Risk:** Use the **Ornstein-Uhlenbeck** model to forecast price volatility.
        *   **Strategy Design:** Price Energy Caps and Collars using Black-Scholes to protect your budget.

        ### **How to Get Started**
        Use the sidebar on the left to navigate through the project phases:
        1.  **Market Data:** Fetch and clean the latest IESO CSV reports.
        2.  **Simulations:** Run Monte Carlo paths to see potential future costs.
        3.  **Hedging Strategy:** Calculate premiums and visualize your "Hedged vs. Unhedged" payoff.
        """)
        
        st.sidebar.info("Select a module above to begin.")

    with tab2:
        # Incorporate the project charter html
        charter_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Financial Digital Twin | Business Summary 2026</title>
            <style>
                :root {
                    --primary: #2c3e50;
                    --accent: #e67e22;
                    --danger: #c0392b;
                    --bg: #f4f7f6;
                }
                body { font-family: 'Segoe UI', sans-serif; background: var(--bg); padding: 10px; line-height: 1.6; }
                .container { max-width: 900px; margin: auto; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
                header { border-bottom: 4px solid var(--primary); margin-bottom: 25px; padding-bottom: 10px; }
                h2 { color: var(--primary); border-left: 5px solid var(--accent); padding-left: 10px; margin-top: 30px; }
                .status-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                .status-table th, .status-table td { padding: 12px; border: 1px solid #ddd; text-align: left; }
                .status-table th { background: #f8f9fa; }
                .error-panel { background: #fdf2f2; border: 1px solid var(--danger); padding: 20px; border-radius: 5px; margin-top: 20px; }
                .error-panel h3 { color: var(--danger); margin-top: 0; }
                .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
                .badge-complete { background: #d4edda; color: #155724; }
                .badge-progress { background: #fff3cd; color: #856404; }
                .badge-pending { background: #e2e3e5; color: #383d41; }
            </style>
        </head>
        <body>
        <div class="container">
            <header>
                <h1>Executive Project Charter: Financial Digital Twin</h1>
                <p>Strategic Risk Modeling for Ontario Industrial Energy Consumers (Market Renewal Era)</p>
            </header>

            <h2>1. Executive Summary</h2>
            <p>This project develops a high-fidelity <strong>Financial Digital Twin</strong> to navigate Ontario's post-2025 Market Renewal environment. By transitioning from HOEP to <strong>Locational Marginal Pricing (LMP)</strong>, the tool enables industrial users to simulate and execute hedging strategies (Caps, Collars, Swaps) to stabilize energy OPEX.</p>

            <h2>2. Business Objectives</h2>
            <ul>
                <li><strong>Risk Mitigation:</strong> Protection against nodal price spikes exceeding $200/MWh.</li>
                <li><strong>Budget Predictability:</strong> Mean-reverting stochastic simulations for 12-month fiscal planning.</li>
                <li><strong>Strategy Engine:</strong> Evaluating "Hedge Effectiveness" against real-time congestion costs.</li>
            </ul>

            <h2>3. Stakeholders</h2>
            <p><strong>Project Sponsor:</strong> Centauri Research | <strong>Primary Users:</strong> CFOs, Energy Managers | <strong>Data:</strong> IESO Public Reports & API</p>

            <h2>4. Mathematical Modelling</h2>
            <p>The simulation engine uses an Ornstein–Uhlenbeck (OU) mean‑reverting stochastic model to represent electricity prices, which naturally spike during grid stress and revert toward structural equilibrium.</p>
            <ul>
                <li><strong>Long-term Mean (μ):</strong> The system's equilibrium HOEP level.</li>
                <li><strong>Reversion Speed (θ):</strong> How quickly prices snap back after volatility events.</li>
                <li><strong>Volatility (σ):</strong> The magnitude of weather‑ and congestion‑driven shocks.</li>
            </ul>

            <h2>5. Project Milestones (2026)</h2>
            <table class="status-table">
                <thead>
                    <tr><th>Phase</th><th>Status</th><th>Target Date</th></tr>
                </thead>
                <tbody>
                    <tr><td>Data Ingestion</td><td><span class="badge badge-complete">✅ Complete</span></td><td>2026-03</td></tr>
                    <tr><td>Risk Modeling (Greeks)</td><td><span class="badge badge-progress">🟡 In Progress</span></td><td>2026-04</td></tr>
                    <tr><td>Strategy Engine</td><td><span class="badge badge-pending">⏳ Pending</span></td><td>2026-05</td></tr>
                    <tr><td>Deployment</td><td><span class="badge badge-pending">⏳ Pending</span></td><td>2026-06</td></tr>
                </tbody>
            </table>

            <div class="error-panel">
                <h3>5. Strategic Vulnerabilities (Missing Logic Links)</h3>
                <p>Current analysis is <strong>non-predictive</strong> and prone to error due to the absence of the following critical physical-financial links:</p>
                <ul>
                    <li><strong>Missing Nodal Correlation (Basis Risk):</strong> The model currently relies on Zonal Averages. Without nodal-specific transmission data, <strong>Delta (&Delta;)</strong> calculations will misrepresent the actual cost at the client's facility by 15-30% during congestion events.</li>
                    <li><strong>Missing Atmospheric Physics (Quantity Risk):</strong> The hedge does not currently ingest <strong>Wind Hub-Height</strong> or <strong>Solar Irradiance</strong> data. This leads to "Quantity Errors" where the volume hedged does not match the volume generated, potentially resulting in forced market buy-backs at peak prices.</li>
                    <li><strong>Linearity Bias (Gamma Risk):</strong> The model assumes price changes are linear. In the Ontario grid, transmission "Shadow Prices" create <strong>Convexity</strong>; once a line hits capacity, the price accelerates exponentially. Without SCED-logic integration, <strong>Gamma (&Gamma;)</strong> is severely underestimated.</li>
                    <li><strong>DART Spread Omission:</strong> Lack of differentiation between Day-Ahead and Real-Time settlement creates a "Slippage Gap" in P&L reporting, as industrial hedges often settle against different time-intervals than physical delivery.</li>
                </ul>
            </div>
        </div>
        </body>
        </html>
        """
        components.html(charter_html, height=850, scrolling=True)

    with tab3:
        # Incorporate the value chain html
        value_chain_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Ontario Energy Market Summary | 2026</title>
            <style>
                :root {
                    --primary: #2c3e50;
                    --secondary: #34495e;
                    --accent: #3498db;
                    --light: #ecf0f1;
                    --border: #bdc3c7;
                    --success: #27ae60;
                }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: var(--primary);
                    background-color: #f4f7f6;
                    margin: 0;
                    padding: 10px;
                }
                .container {
                    max-width: 1000px;
                    margin: auto;
                    background: white;
                    padding: 25px;
                    border-radius: 8px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
                }
                header {
                    border-bottom: 3px solid var(--accent);
                    margin-bottom: 30px;
                    padding-bottom: 10px;
                }
                h1 { margin: 0; color: var(--primary); font-size: 28px; }
                h2 { color: var(--accent); border-left: 5px solid var(--accent); padding-left: 15px; margin-top: 30px; font-size: 20px; }
                .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
                table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 0.9em; }
                th, td { text-align: left; padding: 12px; border-bottom: 1px solid var(--border); }
                th { background-color: var(--light); color: var(--secondary); }
                .highlight-box {
                    background-color: var(--light);
                    padding: 20px;
                    border-radius: 5px;
                    border-left: 5px solid var(--success);
                    margin: 15px 0;
                }
                .formula {
                    background: #273746;
                    color: #d5d8dc;
                    padding: 15px;
                    border-radius: 5px;
                    font-family: 'Courier New', Courier, monospace;
                    text-align: center;
                    margin: 10px 0;
                }
            </style>
        </head>
        <body>
        <div class="container">
            <header>
                <h1>Ontario Energy Market Value Chain & Hedging Brief</h1>
                <p>Strategic Overview: Physics, Regulation, and Financial Greeks</p>
            </header>

            <h2>1. Value Chain Players & Roles</h2>
            <table>
                <thead>
                    <tr>
                        <th>Tier</th>
                        <th>Participants</th>
                        <th>Primary Role</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Generators</strong></td>
                        <td>OPG, Bruce Power, Wind/Solar IPPs</td>
                        <td>Supply electrons via Nuclear, Hydro, Gas, and Renewables.</td>
                    </tr>
                    <tr>
                        <td><strong>Transmitters</strong></td>
                        <td>Hydro One</td>
                        <td>Maintains high-voltage "Highways"; manages physical grid capacity.</td>
                    </tr>
                    <tr>
                        <td><strong>Distributors (LDCs)</strong></td>
                        <td>Toronto Hydro, Alectra</td>
                        <td>"Last-mile" delivery. Non-profit on energy; profit on infrastructure.</td>
                    </tr>
                    <tr>
                        <td><strong>Market Operator</strong></td>
                        <td>IESO</td>
                        <td>The "Air Traffic Controller." Balances 60Hz frequency and runs the auction.</td>
                    </tr>
                    <tr>
                        <td><strong>Brokers/Devs</strong></td>
                        <td>Brookfield, Aggregators</td>
                        <td>Financial facilitators; help small projects reach market scale.</td>
                    </tr>
                </tbody>
            </table>

            <h2>2. Pricing Contracts: Purpose & Protection</h2>
            <div class="grid">
                <div class="highlight-box">
                    <strong>Fixed-Price CfDs (Bruce Power/IESO)</strong>
                    <p>Protects the generator from price crashes. If Market < Contract, IESO pays the gap. If Market > Contract, Generator rebates the excess (clawback).</p>
                </div>
                <div class="highlight-box">
                    <strong>Industrial Hedges (Class A Users)</strong>
                    <p>Protects the consumer from price spikes. Uses Swaps/Options to cap energy costs during peak weather events.</p>
                </div>
            </div>

            <h2>3. Price Determination Logic</h2>
            <ul>
                <li><strong>LCOE (Levelized Cost):</strong> The average total cost to build/operate a plant. Used for long-term planning.</li>
                <li><strong>Spot Market Price:</strong> Set by the <strong>Marginal Generator</strong>. Usually Natural Gas. Every 5 minutes, the most expensive plant needed to meet demand sets the price for everyone.</li>
            </ul>

            <h2>4. Regulatory Pricing (The OEB Layer)</h2>
            <p>The <strong>Ontario Energy Board (OEB)</strong> acts as a buffer between the volatile market and the consumer.</p>
            <div class="highlight-box" style="border-left-color: var(--accent);">
                <strong>Consumer Rate = Forecasted (Gen Costs + Global Adjustment + Delivery)</strong>
            </div>

            <h2>5. The Nodal Price (LMP) Calculation</h2>
            <p>In the 2025 Market Renewal environment, every location has a unique price:</p>
            <div class="formula">
                LMP = System Energy Cost + Transmission Loss + Congestion Shadow Price
            </div>
            <ul>
                <li><strong>Congestion:</strong> The "premium" paid when a cheap path is full, forcing the IESO to use a local, expensive generator.</li>
                <li><strong>Futures Markets:</strong> Move based on anticipated grid "tightness," weather patterns (La Niña/El Niño), and Natural Gas forward curves.</li>
            </ul>

            <h2>6. The Energy Hedging Process (Greeks)</h2>
            <p>Unlike stocks, energy Greeks are driven by <strong>Weather & Physics</strong>:</p>
            <table>
                <thead>
                    <tr>
                        <th>Greek</th>
                        <th>Energy Market Translation</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Delta (&Delta;)</strong></td>
                        <td>Sensitivity to Price/Demand. How value moves with a 100MW demand increase.</td>
                    </tr>
                    <tr>
                        <td><strong>Vega (&nu;)</strong></td>
                        <td>Sensitivity to Supply Volatility (e.g., how unpredictable wind speeds affect costs).</td>
                    </tr>
                    <tr>
                        <td><strong>Theta (&Theta;)</strong></td>
                        <td>Time decay of a hedge, often tied to seasonal reservoir levels (Hydrological Theta).</td>
                    </tr>
                    <tr>
                        <td><strong>Gamma (&Gamma;)</strong></td>
                        <td>Acceleration risk during "Grid Stress" (e.g., price jumping from $40 to $2000).</td>
                    </tr>
                </tbody>
            </table>
        </div>
        </body>
        </html>
        """
        components.html(value_chain_html, height=850, scrolling=True)

# 3. Define Navigation Logic
pages = {
    "Overview": [
        st.Page(show_landing_page, title="Home", icon="🏠"),
    ],
    "Tools": [
        st.Page("pages/1_📊_Market_Data.py", title="Market Data", icon="📊"),
        st.Page("pages/2_📈_Simulations.py", title="Simulations", icon="📈"),
        st.Page("pages/3_💰_Hedging_Strategy.py", title="Hedging Strategy", icon="💰"),
        st.Page("pages/4_📊_Peak_Mitigation.py", title="Peak Mitigation Strategy", icon="📊"),
        st.Page("pages/5_📈_Peak_Analytics.py", title="Peak Analytics", icon="📈"),
        st.Page("pages/6_🌡️_Weather_Cache.py", title="Weather Cache", icon="🌡️"),
        st.Page("pages/7_⚡_IESO_Cache.py", title="IESO Cache", icon="⚡"),
    ]
}

# Run Navigation
pg = st.navigation(pages)
pg.run()

# 4. Add footer branding (Philosophical Insights below navigation)
add_sidebar_footer()
