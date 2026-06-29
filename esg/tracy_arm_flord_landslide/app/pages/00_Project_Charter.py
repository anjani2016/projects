import streamlit as st

st.set_page_config(
    page_title="Project Charter — Tracy Arm Tsunami Twin",
    layout="wide"
)

st.title("🌊 Tracy Arm Fjord Landslide–Tsunami Digital Twin")
st.subheader("Project Charter")

st.markdown("""
## 🎯 Objective of This App
This application allows you to **simulate**, **visualize**, and **compare** landslide‑generated tsunami behaviour inside Alaska’s Tracy Arm Fjord.  
It is designed for engineers, analysts, researchers, and decision‑makers who want to understand:

- How a landslide transfers energy into water  
- How an impulse wave travels through a confined fjord  
- Why the 2025 event produced a **481‑m run‑up**  
- How different modelling engines produce different outcomes  
- How exposure (e.g., vessel proximity) changes risk  

The goal is not only to recreate the 2025 event, but to provide a **scenario‑testing environment** for future hazard assessment.

---

## 🧩 What This App Is *Not*
This is **not** a real‑time hazard warning system.  
It is a **research, education, and risk‑analysis tool** built for exploration and understanding.

---

## 🧠 Philosophy
Extreme natural events are often misunderstood because they are rare, complex, and counter‑intuitive.  
This Digital Twin is built on three principles:

1. **Transparency** — show the physics, not hide it.  
2. **Comparability** — let users see how different models behave.  
3. **Exploration** — encourage “what‑if” thinking to understand risk, not just hazard.

The most powerful events do not always create the biggest disasters — **exposure determines impact**.

---

## 📁 Data Requirements
To run the simulation, the app uses:
- DEM (Digital Elevation Model)  
- Bathymetry  
- Trimline run‑up markers  
- Pre/post‑event elevation change  
- Optional tide‑gauge data  

These will be loaded automatically once placed in the `data/` directory.
            
---
### 🌐 Data Sources

This simulation integrates multiple open geospatial datasets to reconstruct the Tracy Arm fjord environment and support the impulse-wave, propagation, and run‑up models. Each dataset contributes a specific layer of physical realism to the Digital Twin.

#### **1. Elevation (Land DEM)**
High‑resolution elevation data is used to model fjord walls, slope geometry, and run‑up surfaces.
- **ArcticDEM** — 2–8 m stereo-derived elevation mosaics for polar regions  
- **USGS 3DEP** — 1 arc‑second (~30 m) DEM tiles covering Alaska  
- **SRTM** — Global 30 m DEM used as fallback coverage

#### **2. Bathymetry (Seafloor Depth)**
Bathymetric grids define underwater fjord geometry, which strongly influences wave focusing and attenuation.
- **GEBCO** — Global 15 arc‑second bathymetry  
- **NOAA NCEI Coastal Bathymetry** — High‑resolution depth data for U.S. coastal regions  
- **IBCAO** — Arctic Ocean bathymetry (500 m grid)

#### **3. Satellite Imagery & Context Layers**
Imagery provides visual context, glacier front positions, and shoreline geometry.
- **Sentinel‑2** — 10 m multispectral optical imagery  
- **Landsat 8/9** — 30 m multispectral imagery  
- **OpenStreetMap** — Coastlines, fjord outlines, and reference features

#### **4. Environmental & Forcing Data**
Environmental datasets support scenario realism and optional forcing conditions.
- **Open‑Meteo API** — Weather, wind, and atmospheric parameters  
- **NRCan Geospatial Data** — Canadian environmental and terrain datasets (used for cross‑project consistency)

#### **5. Landslide & Run‑Up Validation Data**
These datasets support calibration and validation of the HHF impulse model and NLSWE propagation solver.
- **USGS Landslide Inventory** — Historical landslide records  
- **NASA Earthdata** — Glacier front positions, elevation change, and ice dynamics  
- **Field Run‑Up Measurements** — Observed ~481 m run‑up from the 2015 Tracy Arm event  
- **Peer‑Reviewed Case Studies** — Published analyses of fjord‑generated tsunamis

---

### **Summary**
Together, these datasets provide the terrain, bathymetry, imagery, and physical context required to simulate landslide‑generated tsunamis in Tracy Arm. The Digital Twin architecture is designed so that each dataset can be replaced or upgraded without modifying the simulation engine, ensuring long‑term extensibility and scientific transparency.

---

## 🛠️ Technology Stack & Attributions

This Digital Twin is built on a modern, high-performance open-source scientific stack:
- **UI Framework**: [Streamlit](https://streamlit.io/) for the interactive web dashboard.
- **3D Geospatial Mapping**: Powered by **[pydeck](https://pydeck.gl/)** (the Python wrapper for **[deck.gl](https://deck.gl/)**). 
  - *Special appreciation to **[Dekart](https://dekart.xyz/)** and its founder for pioneering elegant, high-performance deck.gl-based spatial visualizations and inspiring the interactive 3D map layout!*
- **Geospatial & Coordinate Transformations**: [rasterio](https://rasterio.readthedocs.io/) and [pyproj](https://pyproj4.github.io/pyproj/stable/) for reprojecting, clipping, and aligning rasters.
- **Numerical Engines**: [NumPy](https://numpy.org/) and [SciPy](https://scipy.org/) for spatial grids and processing equations.

---

## 🚀 Next Steps
Use the sidebar to navigate to the first module and begin exploring the simulation.
""")
