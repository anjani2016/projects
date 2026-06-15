
import os
import sys

# Ensure project root is in sys.path so that 'src' imports work when deployed
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit as st

st.set_page_config(
    page_title="Tracy Arm Tsunami Twin",
    layout="wide"
)
st.title("🌊 Tracy Arm Tsunami Digital Twin")

st.markdown("""
### This application is organized into a sequence of modules that mirror the physics of a real fjord‑generated tsunami. Each module builds on the previous one, guiding you from landslide initiation to final run‑up analysis.

### **1. Impulse Wave Setup**
Define the landslide characteristics:
- Volume and thickness  
- Impact velocity  
- Failure geometry and slope angle  

These parameters generate the **initial impulse wave** using a high‑fidelity proxy model.

### **2. Wave Propagation**
Simulate how the wave travels through the fjord using a depth‑averaged **Nonlinear Shallow Water Equation (NLSWE)** solver.  
Observe:
- Wave focusing  
- Reflections  
- Energy dissipation  
- Arrival times at key locations  

### **3. Run‑Up Analysis**
Estimate how the wave climbs the fjord walls.  
Compare:
- Modeled run‑up  
- Observed **481‑m run‑up** from the 2015 Tracy Arm event  
- Sensitivity to slope and shoreline geometry  

### **4. Model Comparison**
Evaluate three modeling approaches:
- Empirical scaling laws  
- Numerical NLSWE solver  
- High‑fidelity impulse proxy  

This highlights where models diverge and why.

### **5. Scenario Testing**
Explore “what‑if” conditions:
- Glacier retreat and grounding‑line changes  
- Cruise‑ship proximity and exposure  
- Uncertain landslide volume or impact velocity  

This module demonstrates how hazard and risk evolve under different assumptions.
""")
