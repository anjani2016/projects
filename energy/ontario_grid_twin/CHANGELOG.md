# Changelog: Ontario Grid Digital Twin

All notable changes to this project will be documented in this file.

## [1.3.0] - 2026-05-05
### Added
- **Demo IESO Substation Builder:** Added `data/raw/build_ieso_substations_demo.py` to fetch IESO public transmission interface XML and build a demo substation dataset.
- **Triangulated Demo Geocoding:** Implemented region/city-based triangulation around Ontario regional anchors to create map coordinates when clean station geodata is unavailable.
- **Substation Region Filter:** Added `Substation Regions` sidebar multiselect in `src/pages/1_Interactive_Grid_Map.py` to filter map and analysis scope.

### Changed
- **Generation/Substation Regional Link:** Connected generation source display, flow arcs, and summary totals to the selected substation regions for consistent regional filtering.
- **Generation Filter UX:** Moved generation filter block above simulation parameters and updated labels to include dynamic per-category and total capacity in `MW/day` (1 decimal).
- **Substation Data Preference:** Updated `src/engine/data_loader.py` to prefer `data/raw/ieso_substations_demo.parquet` when present, with explicit internal note that triangulated coordinates are demo-only until clean geocoded data is available.

### Migration Note
- To migrate to clean geocoded substations, replace `data/raw/ieso_substations_demo.parquet` with a validated dataset containing true `geometry` (EPSG:4326) and required fields (`name`, `region`, `capacity_mw`, `current_load_mw`, `headroom_mw`, optional `voltage`).
- Remove or archive `data/raw/build_ieso_substations_demo.py` once a production substation source is established, and keep `src/engine/data_loader.py` pointed at the clean parquet path.

## [1.2.0] - 2026-05-04
### Added
- **Multi-Page Architecture:** Refactored single-script `app.py` into a modular multi-page Streamlit app.
  - `src/main.py`: Entry point and Home/Charter.
  - `src/pages/`: Modularized map, analytics, and project outlook pages.
- **Project Charter:** Added a formal project charter page (`0_Project_Charter.py`) detailing methodology and verified sources.
- **Centralized Data Loader:** Created `src/engine/data_loader.py` to handle shared session state and cached data ingestion.

## [1.1.0] - 2026-05-01
### Added
- **Climate Efficiency Engine:** Implemented non-linear cooling efficiency logic based on ASHRAE TC 9.9 and M-Cycle benchmarks.
- **Effective PUE Metric:** Added calculation for location-specific Power Usage Effectiveness including an 8% cooling floor.
- **Baxtel Harvester:** Created standalone utility `src/utils/baxtel_harvester.py` for live data centre project scraping.
- **Data Source Badge:** UI indicator for active data layer (Baxtel vs National Observer).

## [1.0.0] - 2026-04-30
### Added
- **Monte Carlo Simulation:** Integrated triangular distribution (40% min, 70% typical, 100% peak) for realistic grid reliability modeling.
- **Interactive Grid Map:** High-fidelity PyDeck implementation with dynamic substation reliability coloring.
- **Project Pipeline:** Integrated real-world National Observer (Mar 2026) data for 2,202 MW of proposed hyperscale capacity.
- **Centauri Research Branding:** Integrated corporate logo and professional layout constraints.

### Fixed
- Mapbox API dependency removed in favor of CartoDB built-in styles.
- Fixed `KeyError` in project sorting logic for categorical 'Year' values.
- Resolved tooltip cutoff issues in PyDeck using custom HTML rendering.

## [0.9.0] - 2026-04-28
### Added
- Initial project setup and GIS data processing.
- Basic substation headroom analysis logic.
- Preliminary Monte Carlo script for normal distribution testing.

---
**Technical Note:** This repository is maintained for Advanced Grid Engineering & Data Centre Interconnection Analysis.
