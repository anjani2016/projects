"""
Build comprehensive Ontario generation sources parquet.
Sources:
  - IESO Reliability Outlook (Dec 2025)
  - IESO Supply Mix & Generation page
  - IESO Year-End Data 2025
  - Wikipedia / Natural Resources Canada cross-references
Categories: Nuclear, Hydro, Fossil (Natural Gas/Oil), Renewable (Wind/Solar/Biofuel), Storage
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# ──────────────────────────────────────────────────────────────────────────────
# GENERATION SOURCES — curated from IESO public data
# Fields: name, fuel_type, category, capacity_mw, lat, lon, status, region
# ──────────────────────────────────────────────────────────────────────────────

SOURCES = [
    # ─── NUCLEAR ─────────────────────────────────────────────────────────────
    {"name": "Bruce Power",          "fuel_type": "Nuclear", "category": "Nuclear",
     "capacity_mw": 6430, "lat": 44.32, "lon": -81.60, "status": "Operating",  "region": "Bruce"},
    {"name": "Darlington GS",        "fuel_type": "Nuclear", "category": "Nuclear",
     "capacity_mw": 3524, "lat": 43.88, "lon": -78.71, "status": "Operating",  "region": "Durham"},
    {"name": "Pickering GS",         "fuel_type": "Nuclear", "category": "Nuclear",
     "capacity_mw": 2064, "lat": 43.81, "lon": -79.07, "status": "Operating",  "region": "Durham"},

    # ─── HYDRO ────────────────────────────────────────────────────────────────
    {"name": "Sir Adam Beck 1 & 2",  "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw": 1997, "lat": 43.14, "lon": -79.04, "status": "Operating",  "region": "Niagara"},
    {"name": "Sir Adam Beck Pump Gen","fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":  174, "lat": 43.13, "lon": -79.06, "status": "Operating",  "region": "Niagara"},
    {"name": "Beck Tunnel (OPG)",     "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":  136, "lat": 43.12, "lon": -79.05, "status": "Operating",  "region": "Niagara"},
    {"name": "DeCew Falls GS 1 & 2", "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   91, "lat": 43.17, "lon": -79.26, "status": "Operating",  "region": "Niagara"},
    {"name": "Rankine GS (Niagara)",  "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   18, "lat": 43.09, "lon": -79.06, "status": "Operating",  "region": "Niagara"},
    {"name": "R.H. Saunders GS",     "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":  972, "lat": 44.99, "lon": -74.75, "status": "Operating",  "region": "Eastern"},
    {"name": "Robert H. Saunders (Seaway)", "fuel_type": "Hydro", "category": "Hydro",
     "capacity_mw":  531, "lat": 44.99, "lon": -74.74, "status": "Operating",  "region": "Eastern"},
    {"name": "Healey Falls GS",       "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   14, "lat": 44.41, "lon": -77.62, "status": "Operating",  "region": "Trent-Severn"},
    {"name": "Cameron Falls GS",      "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":  132, "lat": 48.90, "lon": -86.00, "status": "Operating",  "region": "Northern"},
    {"name": "Aguasabon GS",          "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   98, "lat": 48.72, "lon": -86.66, "status": "Operating",  "region": "Northern"},
    {"name": "Alexander GS",          "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   40, "lat": 47.29, "lon": -84.04, "status": "Operating",  "region": "Northern"},
    {"name": "Batchawana GS",         "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   12, "lat": 47.27, "lon": -84.55, "status": "Operating",  "region": "Northern"},
    {"name": "Big Eddy GS",           "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   15, "lat": 49.62, "lon": -94.47, "status": "Operating",  "region": "Northwestern"},
    {"name": "Calabogie GS",          "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   13, "lat": 45.31, "lon": -76.75, "status": "Operating",  "region": "Ottawa Valley"},
    {"name": "Des Joachims GS",       "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":  364, "lat": 46.17, "lon": -77.65, "status": "Operating",  "region": "Ottawa Valley"},
    {"name": "Ear Falls GS",          "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   20, "lat": 50.64, "lon": -93.23, "status": "Operating",  "region": "Northwestern"},
    {"name": "Heli Falls GS",         "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   18, "lat": 48.34, "lon": -85.98, "status": "Operating",  "region": "Northern"},
    {"name": "Kakabeka Falls GS",     "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   26, "lat": 48.40, "lon": -89.62, "status": "Operating",  "region": "Northwestern"},
    {"name": "Manitou Falls GS",      "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   18, "lat": 49.95, "lon": -92.84, "status": "Operating",  "region": "Northwestern"},
    {"name": "Mountain Chute GS",     "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   96, "lat": 45.91, "lon": -77.64, "status": "Operating",  "region": "Ottawa Valley"},
    {"name": "Nipigon GS",            "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":  125, "lat": 49.01, "lon": -88.27, "status": "Operating",  "region": "Northern"},
    {"name": "Otto Holden GS",        "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":  178, "lat": 46.24, "lon": -78.00, "status": "Operating",  "region": "Ottawa Valley"},
    {"name": "Pinard GS",             "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   20, "lat": 47.26, "lon": -83.13, "status": "Operating",  "region": "Northern"},
    {"name": "Plant 1 GS (Sturgeon Falls)", "fuel_type": "Hydro", "category": "Hydro",
     "capacity_mw":   14, "lat": 46.37, "lon": -79.93, "status": "Operating",  "region": "Northern"},
    {"name": "Ragged Chute GS",       "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   18, "lat": 47.43, "lon": -80.27, "status": "Operating",  "region": "Northern"},
    {"name": "Sandy Falls GS",        "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   14, "lat": 46.70, "lon": -80.84, "status": "Operating",  "region": "Northern"},
    {"name": "Stewartville GS",       "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":  104, "lat": 45.69, "lon": -78.18, "status": "Operating",  "region": "Ottawa Valley"},
    {"name": "Whitedog Falls GS",     "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   23, "lat": 49.66, "lon": -94.27, "status": "Operating",  "region": "Northwestern"},
    {"name": "Whitefish Falls GS",    "fuel_type": "Hydro",   "category": "Hydro",
     "capacity_mw":   11, "lat": 46.12, "lon": -81.75, "status": "Operating",  "region": "Northern"},

    # ─── NATURAL GAS (FOSSIL) ─────────────────────────────────────────────────
    {"name": "Portlands Energy Centre", "fuel_type": "Natural Gas", "category": "Fossil",
     "capacity_mw":  550, "lat": 43.64, "lon": -79.34, "status": "Operating",  "region": "Toronto"},
    {"name": "Lennox GS",             "fuel_type": "Natural Gas", "category": "Fossil",
     "capacity_mw": 2100, "lat": 44.26, "lon": -76.79, "status": "Operating",  "region": "Eastern"},
    {"name": "Napanee GS",            "fuel_type": "Natural Gas", "category": "Fossil",
     "capacity_mw":  900, "lat": 44.22, "lon": -76.95, "status": "Operating",  "region": "Eastern"},
    {"name": "Goreway Power Station", "fuel_type": "Natural Gas", "category": "Fossil",
     "capacity_mw":  875, "lat": 43.74, "lon": -79.69, "status": "Operating",  "region": "GTA West"},
    {"name": "Atikokan GS",           "fuel_type": "Natural Gas", "category": "Fossil",
     "capacity_mw":  211, "lat": 48.76, "lon": -91.63, "status": "Operating",  "region": "Northwestern"},
    {"name": "Brighton Beach GS",     "fuel_type": "Natural Gas", "category": "Fossil",
     "capacity_mw":  580, "lat": 42.30, "lon": -83.02, "status": "Operating",  "region": "Southwest"},
    {"name": "Lambton GS",            "fuel_type": "Natural Gas", "category": "Fossil",
     "capacity_mw":  900, "lat": 42.97, "lon": -82.43, "status": "Operating",  "region": "Southwest"},
    {"name": "Lakeview GS (Mississauga)","fuel_type": "Natural Gas", "category": "Fossil",
     "capacity_mw":  300, "lat": 43.56, "lon": -79.55, "status": "Operating",  "region": "GTA West"},
    {"name": "Halton Hills GS",       "fuel_type": "Natural Gas", "category": "Fossil",
     "capacity_mw":  683, "lat": 43.56, "lon": -79.95, "status": "Operating",  "region": "GTA West"},
    {"name": "York Energy Centre",    "fuel_type": "Natural Gas", "category": "Fossil",
     "capacity_mw":  393, "lat": 43.92, "lon": -79.56, "status": "Operating",  "region": "York"},
    {"name": "East Windsor Cogen",    "fuel_type": "Natural Gas", "category": "Fossil",
     "capacity_mw":   72, "lat": 42.32, "lon": -82.97, "status": "Operating",  "region": "Southwest"},
    {"name": "Kirkland Lake GS",      "fuel_type": "Natural Gas", "category": "Fossil",
     "capacity_mw":  120, "lat": 48.14, "lon": -80.03, "status": "Operating",  "region": "Northern"},
    {"name": "Ottawa GS",             "fuel_type": "Natural Gas", "category": "Fossil",
     "capacity_mw":  480, "lat": 45.32, "lon": -75.66, "status": "Operating",  "region": "Eastern"},
    {"name": "Sithe Global Power (GTA)", "fuel_type": "Natural Gas", "category": "Fossil",
     "capacity_mw":  510, "lat": 43.60, "lon": -79.73, "status": "Operating",  "region": "GTA West"},

    # ─── WIND (RENEWABLE) ─────────────────────────────────────────────────────
    {"name": "Wolfe Island Wind",     "fuel_type": "Wind",    "category": "Renewable",
     "capacity_mw":  198, "lat": 44.19, "lon": -76.42, "status": "Operating",  "region": "Eastern"},
    {"name": "Prince Wind Farm",      "fuel_type": "Wind",    "category": "Renewable",
     "capacity_mw":  189, "lat": 46.54, "lon": -84.50, "status": "Operating",  "region": "Northern"},
    {"name": "Dufferin Wind Power",   "fuel_type": "Wind",    "category": "Renewable",
     "capacity_mw":  200, "lat": 44.20, "lon": -80.17, "status": "Operating",  "region": "Southwest"},
    {"name": "Niagara Region Wind",   "fuel_type": "Wind",    "category": "Renewable",
     "capacity_mw":  230, "lat": 43.00, "lon": -79.27, "status": "Operating",  "region": "Niagara"},
    {"name": "K2 Wind Ontario",       "fuel_type": "Wind",    "category": "Renewable",
     "capacity_mw":  270, "lat": 43.77, "lon": -81.09, "status": "Operating",  "region": "Southwest"},
    {"name": "White Pines Wind",      "fuel_type": "Wind",    "category": "Renewable",
     "capacity_mw":   18, "lat": 43.85, "lon": -77.18, "status": "Operating",  "region": "Eastern"},
    {"name": "Bow Lake Wind",         "fuel_type": "Wind",    "category": "Renewable",
     "capacity_mw":  90,  "lat": 47.34, "lon": -82.58, "status": "Operating",  "region": "Northern"},
    {"name": "Armow Wind Ontario",    "fuel_type": "Wind",    "category": "Renewable",
     "capacity_mw":  180, "lat": 44.56, "lon": -81.34, "status": "Operating",  "region": "Bruce"},
    {"name": "Bornish Wind",          "fuel_type": "Wind",    "category": "Renewable",
     "capacity_mw":   99, "lat": 43.05, "lon": -81.46, "status": "Operating",  "region": "Southwest"},
    {"name": "Capstone Infrastructure (Amherst)", "fuel_type": "Wind", "category": "Renewable",
     "capacity_mw":   9,  "lat": 43.92, "lon": -77.90, "status": "Operating",  "region": "Eastern"},
    {"name": "Settlers Landing Wind", "fuel_type": "Wind",    "category": "Renewable",
     "capacity_mw":   78, "lat": 43.42, "lon": -80.31, "status": "Operating",  "region": "Southwest"},
    {"name": "Bluestone Wind",        "fuel_type": "Wind",    "category": "Renewable",
     "capacity_mw":   60, "lat": 43.99, "lon": -81.48, "status": "Operating",  "region": "Bruce"},
    {"name": "Port Ryerse Wind",      "fuel_type": "Wind",    "category": "Renewable",
     "capacity_mw":   10, "lat": 42.75, "lon": -80.18, "status": "Operating",  "region": "Southwest"},
    {"name": "Samsung/Pattern Wind (various)", "fuel_type": "Wind", "category": "Renewable",
     "capacity_mw":  270, "lat": 44.35, "lon": -80.60, "status": "Operating",  "region": "Southwest"},
    {"name": "North Gower Wind",      "fuel_type": "Wind",    "category": "Renewable",
     "capacity_mw":   9,  "lat": 45.07, "lon": -75.71, "status": "Operating",  "region": "Eastern"},
    {"name": "Windlectric (Amherst Island)", "fuel_type": "Wind", "category": "Renewable",
     "capacity_mw":   75, "lat": 44.10, "lon": -76.71, "status": "Operating",  "region": "Eastern"},
    {"name": "Henvey Inlet Wind",     "fuel_type": "Wind",    "category": "Renewable",
     "capacity_mw":  300, "lat": 45.85, "lon": -80.58, "status": "Operating",  "region": "Northern"},

    # ─── SOLAR (RENEWABLE) ────────────────────────────────────────────────────
    {"name": "Samsung-Pattern Solar (Napanee)", "fuel_type": "Solar", "category": "Renewable",
     "capacity_mw":  100, "lat": 44.22, "lon": -76.93, "status": "Operating",  "region": "Eastern"},
    {"name": "Sarnia Photovoltaic Power Plant", "fuel_type": "Solar", "category": "Renewable",
     "capacity_mw":   97, "lat": 42.99, "lon": -82.41, "status": "Operating",  "region": "Southwest"},
    {"name": "Grand Renewable Solar (Haldimand)","fuel_type": "Solar", "category": "Renewable",
     "capacity_mw":  100, "lat": 42.92, "lon": -79.87, "status": "Operating",  "region": "Southwest"},
    {"name": "Guelph Solar",          "fuel_type": "Solar",   "category": "Renewable",
     "capacity_mw":   17, "lat": 43.58, "lon": -80.26, "status": "Operating",  "region": "Southwest"},
    {"name": "Southgate Solar",       "fuel_type": "Solar",   "category": "Renewable",
     "capacity_mw":   17, "lat": 44.14, "lon": -80.73, "status": "Operating",  "region": "Southwest"},
    {"name": "Erin Solar",            "fuel_type": "Solar",   "category": "Renewable",
     "capacity_mw":   10, "lat": 43.78, "lon": -80.07, "status": "Operating",  "region": "Southwest"},
    {"name": "Skypower Solar (various)", "fuel_type": "Solar", "category": "Renewable",
     "capacity_mw":   70, "lat": 43.80, "lon": -79.85, "status": "Operating",  "region": "GTA West"},
    {"name": "Firefly Solar (Lambton)", "fuel_type": "Solar", "category": "Renewable",
     "capacity_mw":   20, "lat": 42.96, "lon": -82.30, "status": "Operating",  "region": "Southwest"},
    {"name": "Thornton Road Solar",   "fuel_type": "Solar",   "category": "Renewable",
     "capacity_mw":   10, "lat": 44.45, "lon": -79.72, "status": "Operating",  "region": "Simcoe"},

    # ─── BIOFUEL (RENEWABLE) ──────────────────────────────────────────────────
    {"name": "Atikokan GS (Biomass)",  "fuel_type": "Biofuel", "category": "Renewable",
     "capacity_mw":  205, "lat": 48.76, "lon": -91.62, "status": "Operating",  "region": "Northwestern"},
    {"name": "Thunder Bay GS (Biomass)","fuel_type": "Biofuel", "category": "Renewable",
     "capacity_mw":  155, "lat": 48.38, "lon": -89.29, "status": "Operating",  "region": "Northwestern"},
    {"name": "Kawartha Dairy Biogas", "fuel_type": "Biofuel", "category": "Renewable",
     "capacity_mw":    3, "lat": 44.30, "lon": -78.20, "status": "Operating",  "region": "Central"},
    {"name": "London Biogas (WM)",    "fuel_type": "Biofuel", "category": "Renewable",
     "capacity_mw":    4, "lat": 42.99, "lon": -81.23, "status": "Operating",  "region": "Southwest"},
    {"name": "Halton Landfill Biogas","fuel_type": "Biofuel", "category": "Renewable",
     "capacity_mw":    2, "lat": 43.57, "lon": -79.99, "status": "Operating",  "region": "GTA West"},

    # ─── ENERGY STORAGE ───────────────────────────────────────────────────────
    {"name": "Oneida Energy Storage", "fuel_type": "Battery",  "category": "Storage",
     "capacity_mw":  250, "lat": 43.02, "lon": -80.52, "status": "Under Construction", "region": "Southwest"},
    {"name": "Mabel Energy Storage",  "fuel_type": "Battery",  "category": "Storage",
     "capacity_mw":  100, "lat": 43.85, "lon": -79.25, "status": "Proposed",    "region": "GTA East"},
    {"name": "Napanee Battery Storage","fuel_type": "Battery", "category": "Storage",
     "capacity_mw":   50, "lat": 44.24, "lon": -76.95, "status": "Operating",   "region": "Eastern"},
]

# ──────────────────────────────────────────────────────────────────────────────
# Build GeoDataFrame and save
# ──────────────────────────────────────────────────────────────────────────────
df = pd.DataFrame(SOURCES)
geometry = [Point(row["lon"], row["lat"]) for _, row in df.iterrows()]
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

# Keep backward-compatible 'type' column aliased to fuel_type
gdf["type"] = gdf["fuel_type"]

out_path = "data/raw/generation_sources.parquet"
gdf.to_parquet(out_path)
print(f"Saved {len(gdf)} generation sources to {out_path}")
print(gdf.groupby(["category", "fuel_type"])["capacity_mw"].sum().to_string())
