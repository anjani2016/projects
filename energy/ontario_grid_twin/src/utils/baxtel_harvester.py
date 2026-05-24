"""
Baxtel Ontario Data Centre Harvester
=====================================
Run this script ONCE (or periodically) to refresh the data centre project list.
Output: data/raw/baxtel_projects.parquet

Usage:
    python src/utils/baxtel_harvester.py
"""

import requests
import pandas as pd
import geopandas as gpd
import os

# Known fallback endpoints to try in order
BAXTEL_ENDPOINTS = [
    "https://baxtel.com/api/v1/map-markers",
    "https://baxtel.com/map/markers.json",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; research-tool/1.0)",
    "Referer": "https://baxtel.com/map",
    "Accept": "application/json",
}

OUTPUT_PATH = "data/raw/baxtel_projects.parquet"


def fetch_baxtel_ontario_data() -> pd.DataFrame | None:
    """
    Attempts to fetch Ontario data centre locations from Baxtel API endpoints.
    Returns a GeoDataFrame if successful, None otherwise.
    """
    for url in BAXTEL_ENDPOINTS:
        print(f"Trying: {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            # Baxtel structure: {'markers': [...]}
            markers_key = next((k for k in ["markers", "data", "results"] if k in data), None)
            if not markers_key:
                print(f"  Unexpected JSON structure from {url}: {list(data.keys())}")
                continue

            df = pd.DataFrame(data[markers_key])
            print(f"  Fetched {len(df)} total records.")

            # Filter Ontario
            for region_col in ["region", "state", "province", "country_subdivision"]:
                if region_col in df.columns:
                    ontario_df = df[df[region_col].str.contains("Ontario", case=False, na=False)].copy()
                    if len(ontario_df) > 0:
                        print(f"  Filtered to {len(ontario_df)} Ontario projects.")
                        break
            else:
                print("  Could not find a region column to filter by.")
                continue

            # Normalise column names to our schema
            rename_map = {
                "power_mw":       "capacity_mw",
                "power":          "capacity_mw",
                "facility_name":  "name",
                "title":          "name",
                "lat":            "latitude",
                "lng":            "longitude",
            }
            ontario_df = ontario_df.rename(columns={k: v for k, v in rename_map.items() if k in ontario_df.columns})

            # Require at minimum: name, latitude, longitude
            required = {"name", "latitude", "longitude"}
            if not required.issubset(ontario_df.columns):
                print(f"  Missing required columns: {required - set(ontario_df.columns)}")
                continue

            # Fill missing capacity with NaN (will be handled in app)
            if "capacity_mw" not in ontario_df.columns:
                ontario_df["capacity_mw"] = float("nan")

            # Add status/year defaults if not present
            if "status" not in ontario_df.columns:
                ontario_df["status"] = "Identified"
            if "year" not in ontario_df.columns:
                ontario_df["year"] = 2026
            if "region" not in ontario_df.columns:
                ontario_df["region"] = "Ontario"

            # Convert to GeoDataFrame
            gdf = gpd.GeoDataFrame(
                ontario_df,
                geometry=gpd.points_from_xy(ontario_df["longitude"], ontario_df["latitude"]),
                crs="EPSG:4326",
            )

            os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
            gdf.to_parquet(OUTPUT_PATH)
            print(f"  Saved to {OUTPUT_PATH}")
            return gdf

        except requests.exceptions.HTTPError as e:
            print(f"  HTTP error: {e}")
        except Exception as e:
            print(f"  Error: {e}")

    print("\nAll endpoints failed. Run this script again later or check Baxtel API access.")
    return None


if __name__ == "__main__":
    result = fetch_baxtel_ontario_data()
    if result is not None:
        print(f"\nSuccess! {len(result)} Ontario data centre projects saved.")
        print(result[["name", "capacity_mw", "region", "status"]].head(10).to_string(index=False))
    else:
        print("\nFetch failed. App will use National Observer fallback data.")
