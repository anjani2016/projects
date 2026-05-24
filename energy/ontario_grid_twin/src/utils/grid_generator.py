import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point
import os

def generate_synthetic_infrastructure():
    print("--- Generating Synthetic Ontario Grid Data ---")
    os.makedirs('data/raw', exist_ok=True)

    # 1. Create Transmission Lines (York Region / Aurora-Newmarket area)
    # Coordinates roughly around 44.0, -79.4
    line_data = [
        {
            'FEATURE_TYPE': 'Hydro Line',
            'VOLTAGE': 500,
            'geometry': LineString([(-79.6, 43.9), (-79.2, 44.1)]) # Major 500kV Trunk
        },
        {
            'FEATURE_TYPE': 'Hydro Line',
            'VOLTAGE': 230,
            'geometry': LineString([(-79.5, 43.8), (-79.5, 44.2)]) # North-South 230kV
        },
        {
            'FEATURE_TYPE': 'Hydro Line',
            'VOLTAGE': 230,
            'geometry': LineString([(-79.7, 44.0), (-79.1, 44.0)]) # East-West 230kV
        }
    ]
    lines_gdf = gpd.GeoDataFrame(line_data, crs="EPSG:4326")
    lines_gdf.to_parquet('data/raw/ontario_lines.parquet')
    print("Success: Created synthetic ontario_lines.parquet")

    # 2. Create Substations (At key intersections/towns)
    substation_data = [
        {'name': 'Armitage TS', 'voltage': '230kV', 'geometry': Point(-79.45, 44.05)},
        {'name': 'Newmarket TS', 'voltage': '230kV', 'geometry': Point(-79.48, 44.03)},
        {'name': 'Aurora South TS', 'voltage': '230kV', 'geometry': Point(-79.43, 43.95)},
        {'name': 'Claireville-York Junction', 'voltage': '500kV', 'geometry': Point(-79.55, 43.90)}
    ]
    subs_gdf = gpd.GeoDataFrame(substation_data, crs="EPSG:4326")
    subs_gdf.to_parquet('data/raw/york_substations.parquet')
    print("Success: Created synthetic york_substations.parquet")

if __name__ == "__main__":
    generate_synthetic_infrastructure()