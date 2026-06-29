import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import os

data = [
    # --- YORK & TORONTO (Existing/Updated) ---
    {"name": "Digital Realty TOR1", "load_mw": 50.0, "lat": 43.639, "lon": -79.375, "Type": "Data Centre", "region": "Toronto"},
    {"name": "Equinix TR2", "load_mw": 35.0, "lat": 43.644, "lon": -79.387, "Type": "Data Centre", "region": "Toronto"},
    {"name": "Microsoft Vaughan DC", "load_mw": 120.0, "lat": 43.834, "lon": -79.501, "Type": "Data Centre", "region": "York"},
    {"name": "Google Toronto Hub", "load_mw": 25.0, "lat": 43.647, "lon": -79.373, "Type": "Data Centre", "region": "Toronto"},
    {"name": "Vaughan Metro Centre DS", "load_mw": 55.0, "lat": 43.794, "lon": -79.527, "Type": "Distribution Substation", "region": "York"},
    {"name": "Markham Centre DS", "load_mw": 80.0, "lat": 43.856, "lon": -79.337, "Type": "Distribution Substation", "region": "York"},
    {"name": "Richmond Hill DS", "load_mw": 65.0, "lat": 43.882, "lon": -79.440, "Type": "Distribution Substation", "region": "York"},
    
    # --- CENTRAL & WEST (Automotive & Logistics) ---
    {"name": "Amazon YYZ1 Brampton", "load_mw": 40.0, "lat": 43.784, "lon": -79.692, "Type": "Logistics Hub", "region": "Central"},
    {"name": "Ford Oakville Assembly", "load_mw": 110.0, "lat": 43.468, "lon": -79.689, "Type": "Industrial", "region": "Central"},
    {"name": "Pearson Airport Hub", "load_mw": 60.0, "lat": 43.677, "lon": -79.624, "Type": "Infrastructure", "region": "Central"},
    {"name": "Toyota Cambridge Plant", "load_mw": 90.0, "lat": 43.435, "lon": -80.334, "Type": "Industrial", "region": "Central"},
    {"name": "Toyota Woodstock Plant", "load_mw": 80.0, "lat": 43.155, "lon": -80.705, "Type": "Industrial", "region": "Southwest"},
    {"name": "Honda Alliston Plant", "load_mw": 95.0, "lat": 44.153, "lon": -79.845, "Type": "Industrial", "region": "Central"},
    {"name": "Stellantis Windsor Assembly", "load_mw": 150.0, "lat": 42.302, "lon": -82.985, "Type": "Industrial", "region": "Southwest"},
    
    # --- NIAGARA & HAMILTON (Steel) ---
    {"name": "Hamilton Steel Cluster", "load_mw": 500.0, "lat": 43.265, "lon": -79.835, "Type": "Industrial", "region": "Niagara"},
    
    # --- EAST (Data Centres & Healthcare) ---
    {"name": "GM Oshawa Assembly", "load_mw": 120.0, "lat": 43.885, "lon": -78.855, "Type": "Industrial", "region": "Eastern"},
    {"name": "Ottawa Kanata DC Cluster", "load_mw": 150.0, "lat": 45.325, "lon": -75.915, "Type": "Data Centre", "region": "Eastern"},
    {"name": "Ottawa Hospital Hub", "load_mw": 40.0, "lat": 45.395, "lon": -75.715, "Type": "Infrastructure", "region": "Eastern"},
    
    # --- NORTH (Mining & Resources) ---
    {"name": "Algoma Steel SSM", "load_mw": 400.0, "lat": 46.525, "lon": -84.365, "Type": "Industrial", "region": "Northern"},
    {"name": "Vale Sudbury Smelter", "load_mw": 300.0, "lat": 46.475, "lon": -81.085, "Type": "Industrial", "region": "Northern"},
    {"name": "Kidd Creek Mine Timmins", "load_mw": 180.0, "lat": 48.475, "lon": -81.325, "Type": "Industrial", "region": "Northern"}
]

df = pd.DataFrame(data)
geometry = [Point(xy) for xy in zip(df.lon, df.lat)]
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

output_path = "data/raw/real_time_demand_centres.parquet"
gdf.to_parquet(output_path)
print(f"Updated {output_path} with {len(df)} Tier 1 demand centres across Ontario.")
