# Changelog - Lake Digital Twin

## [v2.3] - 2026-06-22
### Added
- **Inspection Alerts Engine**: Created `models/inspection_engine.py` to evaluate composite risk criteria (runoff, stratification, satellite spikes) and trigger alerts.
- **Inspection Center View**: Added `views/5_Inspection_Alerts.py` featuring interactive simulation inputs and field team dispatch cards.
- **Gemini AI Integration**: Implemented live Gemini API requests for generating environmental briefs.
- **Interactive Workflow**: Realigned the Project Charter (`views/1_Project_Charter.py`) into a clean workflow representation using native Streamlit containers.

## [v2.2] - 2026-05-03
### Added
- **Project Charter**: New page `1_Project_Charter.py` added to the Overview section.

### Changed
- **Reindexed Navigation**: Reorganized the app structure to follow the new numerical indexing (0-3).
- **Page Renames**: Moved Predictive Risk Model to `3_Monte_Carlo_Sim.py` to maintain sequential flow.

---

## [v2.1] - 2026-05-03

## [v1] - 2026-05-01
### Added
- **3D Bathymetry**: Initial implementation of 3D mesh rendering for lake beds.
- **Chemical Engine**: Thermodynamic equilibrium modeling and Saturation Index (SI) calculations.
- **Risk Model**: Monte Carlo simulation for predictive risk analysis.
- **Dockerization**: Initial Dockerfile setup with WhiteboxTools integration.
