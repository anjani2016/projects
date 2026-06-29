import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString
import os

def generate_enhanced_grid():
    print("--- Generating Enhanced Ontario Grid Infrastructure ---")
    os.makedirs('data/raw', exist_ok=True)

    # 1. Generation Sources
    gen_data = [
        {'name': 'Bruce Power', 'type': 'Nuclear', 'lat': 44.32, 'lon': -81.60, 'capacity_mw': 6550},
        {'name': 'Darlington', 'type': 'Nuclear', 'lat': 43.88, 'lon': -78.71, 'capacity_mw': 3500},
        {'name': 'Sir Adam Beck', 'type': 'Hydro', 'lat': 43.14, 'lon': -79.04, 'capacity_mw': 1997}
    ]
    gen_df = pd.DataFrame(gen_data)
    gen_gdf = gpd.GeoDataFrame(gen_df, geometry=gpd.points_from_xy(gen_df.lon, gen_df.lat), crs="EPSG:4326")
    gen_gdf.to_parquet('data/raw/generation_sources.parquet')

    # 2. Existing Data Centres (Clusters)
    dc_data = [
        {'name': 'Vaughan Cluster', 'load_mw': 450, 'lat': 43.81, 'lon': -79.53},
        {'name': 'Toronto Downtown', 'load_mw': 300, 'lat': 43.64, 'lon': -79.38},
        {'name': 'Markham Hub', 'load_mw': 200, 'lat': 43.85, 'lon': -79.33}
    ]
    dc_df = pd.DataFrame(dc_data)
    dc_gdf = gpd.GeoDataFrame(dc_df, geometry=gpd.points_from_xy(dc_df.lon, dc_df.lat), crs="EPSG:4326")
    dc_gdf.to_parquet('data/raw/existing_dc.parquet')
    
    print("Success: Enhanced grid layers saved.")

if __name__ == "__main__":
    generate_enhanced_grid()