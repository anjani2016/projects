import os
import geopandas as gpd
from shapely.geometry import Point

def initialize_project():
    # Define folder structure
    folders = [
        'data/raw',
        'data/processed',
        'src/engine',
        'src/utils'
    ]
    
    print("--- Initializing Ontario Digital Twin Workspace ---")
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"Created: {folder}")

    # Basic GIS Health Check
    try:
        d = {'col1': ['check'], 'geometry': [Point(1, 2)]}
        gdf = gpd.GeoDataFrame(d, crs="EPSG:4326")
        print("GIS Library Status: [OK] GeoPandas and Shapely are functional.")
    except Exception as e:
        print(f"GIS Library Status: [ERROR] {e}")

if __name__ == "__main__":
    initialize_project()