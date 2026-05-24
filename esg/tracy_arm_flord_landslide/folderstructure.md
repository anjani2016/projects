# 📁 Project Folder Structure — Summary & Responsibilities

This document describes the purpose of each folder and module inside the `src/` directory.  
Every folder contains an `__init__.py` file so the entire tree functions as a Python package.

---

## 🏛️ `src/`
Top‑level Python package containing all simulation logic, geospatial utilities, physics engines, and helper modules used by the Streamlit app.

---

## 🌍 `src/geospatial/`
Modules responsible for loading, processing, and preparing geospatial datasets, as well as constructing the computational domain.

### **Files**
- **`dem_loader.py`**  
  Loads, clips, masks, and preprocesses **Digital Elevation Models (DEM)**.  
  Produces elevation arrays + coordinate grids for simulation.

- **`bathymetry_loader.py`**  
  Loads and preprocesses **bathymetry** (underwater depth).  
  Ensures alignment with DEM and handles no‑data regions.

- **`fjord_geometry.py`**  
  Analyzes and extracts specific topographic/geometric features of the fjord walls and shoreline.

- **`mesh_builder.py`**  
  Generates computational grids (X, Y, Z arrays) from merged DEM + bathymetry.

---

## 🚀 `src/engines/`
Numerical solvers and empirical models that drive the core simulations.

### **Files**
- **`hhf.py` & `hhf_1.py`**  
  Implements the **Heller–Hager–Fritz (HHF) proxy** to generate the initial impulse wave field (η₀) based on landslide parameters.

- **`nlswe.py` & `nlswe_1.py`**  
  Numerical solvers for the **Nonlinear Shallow Water Equations (NLSWE)**.  
  Handles time-stepped wave propagation, reflections, focusing, and energy transport down the fjord.

- **`boussinesq_proxy.py`**  
  High-fidelity wave proxy modeling.

---

## 🌊 `src/physics/`
Core physical formulas and phenomenological models supporting the engines.

### **Files**
- **`impulse.py`**  
  Mathematical definitions and physics formulations for wave initiation.

- **`runup.py`**  
  Computes shoreline wave run‑up using steep-slope geometry and wave amplitude.

- **`friction.py`**  
  Handles bottom friction calculations (e.g., Manning's *n*) affecting wave energy dissipation.

---

## 🧰 `src/utils/`
General‑purpose helper functions, configuration, and shared utilities.

### **Files**
- **`config.py`**  
  Centralized configuration, paths, and environment settings.

- **`data_processor.py`**  
  Handles data transformation, normalizing datasets, and preparing inputs for the models.

- **`numerics.py`**  
  Shared mathematical and numerical helper functions used across different solvers.

- **`logging.py`**  
  Logging utilities for debugging, diagnostics, and tracking simulation progress.

---

# 📌 Summary

The `src/` directory is structured as a modular scientific computing package tailored specifically for this Digital Twin:

- **geospatial/** → data ingestion, domain geometry, and mesh building
- **engines/** → solvers for impulse waves and NLSWE propagation  
- **physics/** → core mathematical formulas (friction, runup, impulse)  
- **utils/** → shared helpers, data processing, and config  

*(Note: Visualization is handled natively in the Streamlit `app/` pages, and `tests/` reside at the root level of the repository, reducing redundancy in the `src/` directory).*
