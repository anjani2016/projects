"""
Ontario Lakes Reference Dataset
Source: Ontario GeoHub, Ontario Lake Partner Program (LPP), NRCan HRDEM
Curated for use in the Lake Health Digital Twin.

Each lake includes:
  - Geolocation (center lat/lon)
  - Morphometry (area_km2, max_depth_m, mean_depth_m)
  - Catchment characteristics (catchment_area_km2, agri_pct)
  - Baseline chemistry (tp_baseline, ph_baseline, ca_baseline)
  - Trophic state classification
  - Conservation Authority
"""

ONTARIO_LAKES = [
    {
        "name": "Lake Simcoe",
        "lat": 44.3900, "lon": -79.4200,
        "area_km2": 722, "max_depth_m": 41, "mean_depth_m": 15,
        "catchment_area_km2": 2990, "agri_pct": 35,
        "tp_baseline": 0.072, "ph_baseline": 8.2, "ca_baseline": 42.0,
        "trophic_state": "Mesotrophic",
        "conservation_authority": "Lake Simcoe Region CA",
        "region": "York / Simcoe",
        "notes": "Subject to Ontario's Lake Simcoe Protection Plan (2009)."
    },
    {
        "name": "Lake Muskoka",
        "lat": 44.9900, "lon": -79.5800,
        "area_km2": 125, "max_depth_m": 116, "mean_depth_m": 25,
        "catchment_area_km2": 465, "agri_pct": 5,
        "tp_baseline": 0.006, "ph_baseline": 7.3, "ca_baseline": 5.5,
        "trophic_state": "Oligotrophic",
        "conservation_authority": "Muskoka Watershed Council",
        "region": "Muskoka",
        "notes": "Soft-water Canadian Shield lake, very low nutrient baseline."
    },
    {
        "name": "Rice Lake",
        "lat": 44.1200, "lon": -78.2200,
        "area_km2": 79, "max_depth_m": 10, "mean_depth_m": 4,
        "catchment_area_km2": 4720, "agri_pct": 45,
        "tp_baseline": 0.052, "ph_baseline": 8.0, "ca_baseline": 55.0,
        "trophic_state": "Eutrophic",
        "conservation_authority": "Otonabee Region CA",
        "region": "Peterborough",
        "notes": "Shallow, highly productive lake with significant agricultural loading."
    },
    {
        "name": "Kempenfelt Bay (Lake Simcoe)",
        "lat": 44.3600, "lon": -79.6800,
        "area_km2": 42, "max_depth_m": 21, "mean_depth_m": 9,
        "catchment_area_km2": 210, "agri_pct": 28,
        "tp_baseline": 0.085, "ph_baseline": 8.3, "ca_baseline": 40.0,
        "trophic_state": "Eutrophic",
        "conservation_authority": "Lake Simcoe Region CA",
        "region": "Barrie",
        "notes": "Innermost bay of Lake Simcoe, highest nutrient loading in the system."
    },
    {
        "name": "Lake Rosseau",
        "lat": 45.1900, "lon": -79.6200,
        "area_km2": 67, "max_depth_m": 76, "mean_depth_m": 18,
        "catchment_area_km2": 185, "agri_pct": 4,
        "tp_baseline": 0.007, "ph_baseline": 7.1, "ca_baseline": 4.8,
        "trophic_state": "Oligotrophic",
        "conservation_authority": "Muskoka Watershed Council",
        "region": "Muskoka",
        "notes": "Connected to Lakes Joseph and Muskoka via locks."
    },
    {
        "name": "Scugog Lake",
        "lat": 44.1700, "lon": -78.9300,
        "area_km2": 63, "max_depth_m": 5, "mean_depth_m": 2,
        "catchment_area_km2": 1010, "agri_pct": 55,
        "tp_baseline": 0.095, "ph_baseline": 8.1, "ca_baseline": 60.0,
        "trophic_state": "Eutrophic",
        "conservation_authority": "Central Lake Ontario CA",
        "region": "Durham",
        "notes": "Very shallow eutrophic lake, chronic blue-green algae blooms."
    },
    {
        "name": "Balsam Lake",
        "lat": 44.6000, "lon": -78.8700,
        "area_km2": 26, "max_depth_m": 19, "mean_depth_m": 7,
        "catchment_area_km2": 95, "agri_pct": 12,
        "tp_baseline": 0.015, "ph_baseline": 7.6, "ca_baseline": 18.0,
        "trophic_state": "Mesotrophic",
        "conservation_authority": "Kawartha Conservation",
        "region": "Kawartha Lakes",
        "notes": "Head of the Trent-Severn Waterway."
    },
    {
        "name": "Lake of Bays",
        "lat": 45.2900, "lon": -79.0100,
        "area_km2": 64, "max_depth_m": 83, "mean_depth_m": 20,
        "catchment_area_km2": 215, "agri_pct": 3,
        "tp_baseline": 0.005, "ph_baseline": 7.0, "ca_baseline": 4.2,
        "trophic_state": "Oligotrophic",
        "conservation_authority": "Muskoka Watershed Council",
        "region": "Muskoka",
        "notes": "Deep Canadian Shield lake with pristine water quality."
    },
    {
        "name": "Sturgeon Lake",
        "lat": 44.5600, "lon": -78.7100,
        "area_km2": 90, "max_depth_m": 22, "mean_depth_m": 7,
        "catchment_area_km2": 330, "agri_pct": 18,
        "tp_baseline": 0.025, "ph_baseline": 7.8, "ca_baseline": 25.0,
        "trophic_state": "Mesotrophic",
        "conservation_authority": "Kawartha Conservation",
        "region": "Kawartha Lakes",
        "notes": "Part of the Trent-Severn system; moderate agricultural influence."
    },
    {
        "name": "Chemong Lake",
        "lat": 44.3900, "lon": -78.4400,
        "area_km2": 22, "max_depth_m": 9, "mean_depth_m": 3,
        "catchment_area_km2": 480, "agri_pct": 42,
        "tp_baseline": 0.065, "ph_baseline": 8.1, "ca_baseline": 48.0,
        "trophic_state": "Eutrophic",
        "conservation_authority": "Otonabee Region CA",
        "region": "Peterborough",
        "notes": "Shallow, productive lake with high agricultural P loading."
    },
]

def get_lake_by_name(name: str) -> dict | None:
    """Returns lake data dictionary by exact name match."""
    for lake in ONTARIO_LAKES:
        if lake["name"] == name:
            return lake
    return None

def get_trophic_color(trophic_state: str) -> str:
    """Returns a folium-compatible colour for trophic state markers."""
    return {
        "Oligotrophic": "blue",
        "Mesotrophic": "green",
        "Eutrophic": "red",
    }.get(trophic_state, "gray")
