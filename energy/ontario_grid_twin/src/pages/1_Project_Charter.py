import streamlit as st
import pandas as pd
from energy.ontario_grid_twin.src.utils.ui_branding import apply_branding

apply_branding()

# Check if data is loaded (optional for this static-ish page, but good for consistency)
if 'data_loaded' not in st.session_state:
    st.warning("Application data is not yet initialized. Return to Home to load data if needed.")

def render_project_charter():
    st.title("📋 Project Charter:")
    st.subheader("Digital twin for large step load interconnection screening")
    
    st.markdown("""
    **Purpose:** Provide a practical planning-grade sandbox to evaluate where large
    new loads (e.g., data centres, EV charging stations, etc) can be connected with acceptable reliability risk,
    available headroom, and transparent engineering assumptions.
    """)

    st.markdown("""
### **The Grid Balancing Act**
At its core, the power grid is a massive, real-time machine where **Supply must perfectly match Demand** every second. If this balance shifts, the grid loses reliability.

### **The Challenge: The Era of Electrification**
The rapid expansion of **AI Data Centres** and the mass adoption of **Electric Vehicles (EVs)** are driving an unprecedented surge in demand. This "Electrification" transition requires a level of grid planning that is more dynamic than ever before.

### **How to Use This Digital Twin**
This application functions as a "Flight Simulator" for the Ontario Power Grid. It allows you to:
* **Explore the Map:** Visualize the "Power Journey" from Generators and Transmission Nodes (HV) to local Demand Centres.
* **Stress Test the Grid:** Simulate new "Step Loads" (like a 200MW Data Centre) to see where the system hits its thermal limits.
* **Analyze Reliability:** Run **Monte Carlo Simulations** to calculate the statistical probability of a node failure under different climate and load scenarios.

**Goal:** Bridge the gap between raw energy data and actionable engineering insights.
""")
    
    st.markdown("### 🛠️ Project Methodology")
    
    st.markdown("""
We integrate macro-energy trends with micro-facility data to create a unified provincial grid view using a five-stage technical pipeline:
    """)

    st.markdown("""
#### 1. Data Ingestion & Synthesis
- **Supply-Side Ingestion**: Automated parsing of IESO Market Data (Nuclear, Hydro, Wind, Gas) and CER Energy Future 2026 scenarios.
- **Demand-Side Synthesis**: Mapping hyperscale project pipelines (Baxtel/National Observer) against regional peak demand forecasts.

#### 2. Probabilistic Reliability Modeling
Rather than relying on static "Worst Case" scenarios, the system utilizes a **Monte Carlo Simulation** engine.
- **Stochastic Sampling**: Load profiles are modeled using **Triangular Distributions** (Min, Mode, Max) to account for operational variance.
- **Convergence**: 10,000+ iterations are run to determine the probability of "Headroom Breach" at key substations.

#### 3. Climate-Adjusted Efficiency Analysis
A non-linear thermal model is applied to reflect real-world data center energy behavior.
- **IESO July 2025 Calibration**: Applying the 44% peak cooling overhead identified in the "Large Step Loads" technical paper.
- **Dynamic PUE Mapping**: Cooling efficiency factors are adjusted based on ambient temperature data from the Open-Meteo API.

#### 4. Spatial Analytics & Visualization
- **Multi-Tier Mapping**: Leveraging `pydeck` for high-performance visualization of supply/demand proximity.
- **Regional Hierarchies**: Data is classified into Transmission (Red), Regional (Orange), and Demand Centres (Green) to identify bottlenecks at the correct layer.

#### 5. Verification & Validation
- **Benchmark Comparison**: Simulation outputs are cross-referenced against the IESO 2026 Annual Planning Outlook (APO).
- **Engineering Logic**: Adheres to ASHRAE TC 9.9 thermal classes and Ontario Energy Board (OEB) load capacity frameworks.
    """)


    st.divider()

    st.markdown("### Smart Grid  & Energy Distribution & ")
    st.caption(
        "Energy flows from the power generators to consumers through a series of transformers classified in this model as 'Transmission Substations', 'Regional Transformer Stations', and 'Demand Centres'"
    )

    # Create two columns for side-by-side display
    col1, col2 = st.columns(2)

    with col1:
        st.image(
            "data/assets/smart_grid.jpeg",
            caption="Figure 1 - Smart Grid Overview",
            use_container_width=True,
        )

    with col2:
        st.image(
            "data/assets/energy_distribution_schematic.png",
            caption="Figure 2 - Distribution Schematic",
            use_container_width=True,
        )

    st.divider()
    st.markdown("### 🧭 IESO Large Step Loads Schematic")
    st.caption(
        "Reference: IESO Demand & Conservation Planning Technical Paper - Large Step Loads (July 2025), "
        "Figure 3 (page 7)."
    )
    # Internal note: this image is rendered from a local PDF snapshot for demo reproducibility.
    # Replace with a clean, versioned asset workflow if/when IESO provides a canonical image endpoint.
    st.image(
        "data/assets/datacentre_components.png",
        caption="Figure 3 - Large Step Loads planning schematic (IESO, Jul 2025)",
        use_container_width=True,
    )
    st.markdown(
        "[View source document (IESO PDF)]"
        "(https://www.ieso.ca/-/media/Files/IESO/Document-Library/planning-forecasts/demand-research/"
        "Demand-Conservation-Planning-Technical-Paper-Large-Step-Loads-202507.pdf)"
    )

    st.divider()
    st.markdown("### ❄️ Cooling Efficiency Reference")
    st.info("Model: Non-Linear Evaporative Cooling with an 8% Fixed Cooling Floor.")
    
    efficiency_data = [
        {"Range": "10 to 20°C", "Savings": "10%", "Mode": "Evaporative Support"},
        {"Range": "0 to 10°C", "Savings": "30%", "Mode": "Partial Free Cooling"},
        {"Range": "-10 to 0°C", "Savings": "50%", "Mode": "Full Free Cooling"},
        {"Range": "-20 to -10°C", "Savings": "70%", "Mode": "Peak Efficiency"}
    ]
    st.dataframe(pd.DataFrame(efficiency_data), use_container_width=True)

    st.caption("Developed by: Centauri Research / Advanced Grid Engineering")

if __name__ == "__main__":
    render_project_charter()