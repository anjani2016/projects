import os
import requests
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
import time

# Configuration for York Region (Approximate Bounding Box)
YORK_BBOX = "43.8,-79.7,44.2,-79.2" 

def download_transmission_lines():
    """
    Downloads high-voltage line data from a more stable NRCan GeoJSON source.
    """
    print("Step 1: Downloading Transmission Lines...")
    # Updated link to the National Power Grid dataset
    url = "https://services3.arcgis.com/Z66Y9H68V7Y8T98A/arcgis/rest/services/Electricity_Transmission_Lines/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        lines = gpd.read_file(response.text)
        
        # Filter for Ontario specifically if the dataset is national
        if 'PROVINCE' in lines.columns:
            lines = lines[lines['PROVINCE'] == 'ON']
            
        lines.to_parquet('data/raw/ontario_lines.parquet')
        print(f"Success: Saved {len(lines)} line segments.")
    except Exception as e:
        print(f"Error downloading lines: {e}")
        print("Note: If the URL failed, we will create a dummy file for development in the next step.")

def fetch_substations_osm():
    """
    Queries OSM with headers and a check for valid JSON.
    """
    print("Step 2: Fetching York Region Substations from OSM...")
    overpass_url = "https://overpass-api.de/api/interpreter" # Changed to https
    
    overpass_query = f"""
    [out:json][timeout:25];
    (
      node["power"="substation"]({YORK_BBOX});
      way["power"="substation"]({YORK_BBOX});
    );
    out center;
    """
    
    headers = {
        'User-Agent': 'OntarioDigitalTwinProject/1.0',
        'Accept': 'application/json'
    }

    try:
        response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers)
        
        if response.status_code != 200:
            print(f"Server returned error {response.status_code}: {response.text}")
            return

        data = response.json()
        
        if 'elements' not in data or len(data['elements']) == 0:
            print("No substations found in this bounding box.")
            return

        nodes = []
        for element in data['elements']:
            geom = element.get('center') if 'center' in element else {'lon': element.get('lon'), 'lat': element.get('lat')}
            
            if geom['lon'] and geom['lat']:
                nodes.append({
                    'name': element.get('tags', {}).get('name', 'Unnamed Substation'),
                    'voltage': element.get('tags', {}).get('voltage', 'Unknown'),
                    'geometry': shape({'type': 'Point', 'coordinates': [geom['lon'], geom['lat']]})
                })
        
        substations = gpd.GeoDataFrame(nodes, crs="EPSG:4326")
        substations.to_parquet('data/raw/york_substations.parquet')
        print(f"Success: Saved {len(substations)} substations.")
        
    except Exception as e:
        print(f"Error fetching substations: {e}")

def create_mock_ieso_2026_data():
    """
    Creates a structured 2026 forecast.
    """
    print("Step 3: Generating IESO 2026 Forecast Template...")
    data = {
        'region': ['York', 'Toronto', 'Ottawa', 'Niagara'],
        'peak_demand_mw_2026': [4200, 5100, 1800, 1200],
        'available_capacity_mw': [5000, 5500, 2200, 1500],
        'growth_scenario': ['High', 'Reference', 'Reference', 'Low']
    }
    df = pd.DataFrame(data)
    df.to_csv('data/raw/ieso_2026_forecast.csv', index=False)
    print("Success: Generated ieso_2026_forecast.csv")

if __name__ == "__main__":
    # Ensure data folder exists
    os.makedirs('data/raw', exist_ok=True)
    
    download_transmission_lines()
    time.sleep(2) # Brief pause to be kind to servers
    fetch_substations_osm()
    create_mock_ieso_2026_data()