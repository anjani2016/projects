import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import os

data = [
    # --- TRANSMISSION (Red) - Major Switching/HV Hubs ---
    {"name": "Claireville SS", "voltage": "500kV", "lat": 43.76, "lon": -79.63, "region": "Central"},
    {"name": "Cherrywood SS", "voltage": "500kV", "lat": 43.88, "lon": -79.13, "region": "Eastern"},
    {"name": "Trafalgar SS", "voltage": "500kV", "lat": 43.55, "lon": -79.78, "region": "Central"},
    {"name": "Beck SS", "voltage": "230kV", "lat": 43.14, "lon": -79.05, "region": "Niagara"},
    {"name": "Manby SS", "voltage": "230kV", "lat": 43.62, "lon": -79.52, "region": "Toronto"},
    {"name": "Leaside SS", "voltage": "230kV", "lat": 43.70, "lon": -79.35, "region": "Toronto"},
    {"name": "Essa SS", "voltage": "500kV", "lat": 44.30, "lon": -79.75, "region": "Central"},
    {"name": "Hanmer SS", "voltage": "500kV", "lat": 46.65, "lon": -80.95, "region": "Northern"},
    {"name": "Wawa SS", "voltage": "230kV", "lat": 47.98, "lon": -84.75, "region": "Northern"},
    {"name": "Mackenzie SS", "voltage": "230kV", "lat": 48.45, "lon": -89.20, "region": "Northwestern"},
    {"name": "Hawthorne SS", "voltage": "230kV", "lat": 45.38, "lon": -75.60, "region": "Eastern"},
    {"name": "Minden SS", "voltage": "230kV", "lat": 44.92, "lon": -78.72, "region": "Central"},
    {"name": "Nanticoke SS", "voltage": "500kV", "lat": 42.80, "lon": -80.05, "region": "Southwest"},
    {"name": "Bruce SS", "voltage": "500kV", "lat": 44.33, "lon": -81.55, "region": "Bruce"},
    
    # --- REGIONAL TS (Orange) - Major City/Regional Supply ---
    # York Region
    {"name": "Armitage TS", "voltage": "230kV", "lat": 44.03, "lon": -79.47, "region": "York"},
    {"name": "Newmarket TS", "voltage": "230kV", "lat": 44.05, "lon": -79.43, "region": "York"},
    {"name": "Aurora South TS", "voltage": "230kV", "lat": 43.98, "lon": -79.45, "region": "York"},
    {"name": "Vaughan TS", "voltage": "230kV", "lat": 43.82, "lon": -79.55, "region": "York"},
    {"name": "Markham TS", "voltage": "230kV", "lat": 43.87, "lon": -79.30, "region": "York"},
    {"name": "Kleinburg TS", "voltage": "230kV", "lat": 43.84, "lon": -79.62, "region": "York"},
    {"name": "Buttonville TS", "voltage": "230kV", "lat": 43.86, "lon": -79.35, "region": "York"},
    
    # Toronto
    {"name": "Bridgman TS", "voltage": "115kV", "lat": 43.67, "lon": -79.41, "region": "Toronto"},
    {"name": "Strachan TS", "voltage": "115kV", "lat": 43.64, "lon": -79.41, "region": "Toronto"},
    {"name": "Main TS", "voltage": "115kV", "lat": 43.68, "lon": -79.30, "region": "Toronto"},
    {"name": "Wiltshire TS", "voltage": "115kV", "lat": 43.66, "lon": -79.45, "region": "Toronto"},
    {"name": "Hearn TS", "voltage": "115kV", "lat": 43.62, "lon": -79.33, "region": "Toronto"},
    
    # Peel/Halton
    {"name": "Bramalea TS", "voltage": "230kV", "lat": 43.72, "lon": -79.70, "region": "Central"},
    {"name": "Mississauga TS", "voltage": "230kV", "lat": 43.58, "lon": -79.65, "region": "Central"},
    {"name": "Oakville TS", "voltage": "230kV", "lat": 43.45, "lon": -79.72, "region": "Central"},
    {"name": "Burlington TS", "voltage": "230kV", "lat": 43.35, "lon": -79.82, "region": "Central"},
    
    # Durham
    {"name": "Whitby TS", "voltage": "230kV", "lat": 43.90, "lon": -78.95, "region": "Eastern"},
    {"name": "Oshawa TS", "voltage": "230kV", "lat": 43.92, "lon": -78.85, "region": "Eastern"},
    {"name": "Clarington TS", "voltage": "500kV", "lat": 43.95, "lon": -78.70, "region": "Eastern"},
    
    # Other Major Hubs
    {"name": "London TS", "voltage": "230kV", "lat": 42.98, "lon": -81.25, "region": "Southwest"},
    {"name": "Windsor TS", "voltage": "230kV", "lat": 42.30, "lon": -83.00, "region": "Southwest"},
    {"name": "Sarnia TS", "voltage": "230kV", "lat": 42.95, "lon": -82.40, "region": "Southwest"},
    {"name": "Kitchener TS", "voltage": "230kV", "lat": 43.45, "lon": -80.48, "region": "Southwest"},
    {"name": "Guelph TS", "voltage": "230kV", "lat": 43.55, "lon": -80.25, "region": "Southwest"},
    {"name": "Kingston TS", "voltage": "230kV", "lat": 44.25, "lon": -76.50, "region": "Eastern"},
    {"name": "Sudbury TS", "voltage": "230kV", "lat": 46.50, "lon": -81.00, "region": "Northern"},
    {"name": "Timmins TS", "voltage": "230kV", "lat": 48.48, "lon": -81.33, "region": "Northern"},
    {"name": "Sault Ste Marie TS", "voltage": "230kV", "lat": 46.53, "lon": -84.35, "region": "Northern"},
    {"name": "Thunder Bay TS", "voltage": "230kV", "lat": 48.40, "lon": -89.25, "region": "Northwestern"},
    {"name": "Kenora TS", "voltage": "230kV", "lat": 49.77, "lon": -94.48, "region": "Northwestern"},
    {"name": "Cornwall TS", "voltage": "230kV", "lat": 45.02, "lon": -74.73, "region": "Eastern"},
    {"name": "Belleville TS", "voltage": "230kV", "lat": 44.17, "lon": -77.38, "region": "Eastern"},
    {"name": "Barrie TS", "voltage": "230kV", "lat": 44.38, "lon": -79.68, "region": "Central"},
    {"name": "Orangeville TS", "voltage": "230kV", "lat": 43.92, "lon": -80.10, "region": "Central"}
]

# Merge with the existing IESO demo backbone to ensure we don't lose the interface limits
demo_path = "data/raw/ieso_substations_demo.parquet"
if os.path.exists(demo_path):
    demo_df = pd.read_parquet(demo_path)
    # Filter out any that we've redefined with better coordinates/names if needed
    # For now, just combine them
    combined_data = data + demo_df[['name', 'voltage', 'lat', 'lon', 'region']].to_dict('records')
    df = pd.DataFrame(combined_data)
    # Remove duplicates by name
    df = df.drop_duplicates(subset=['name'])
else:
    df = pd.DataFrame(data)

# Add dummy capacity/load for new ones if missing
if 'capacity_mw' not in df.columns: df['capacity_mw'] = 1000.0
if 'current_load_mw' not in df.columns: df['current_load_mw'] = 600.0
if 'headroom_mw' not in df.columns: df['headroom_mw'] = 400.0

geometry = [Point(xy) for xy in zip(df.lon, df.lat)]
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

output_path = "data/raw/ieso_substations_demo.parquet"
gdf.to_parquet(output_path)
print(f"Populated comprehensive grid with {len(df)} stations across Ontario.")
