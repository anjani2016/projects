"""
Build a demo Ontario substation dataset from IESO public transmission interfaces.

Why this exists:
- IESO public XML reports expose interface/facility names and limits, but not a clean
  geocoded substation master with precise lat/lon for each station.
- For demo UX, this script infers a region/city from interface names, then assigns
  synthetic map points around regional anchors using a triangular pattern.

When clean geospatial substation data becomes available:
- Replace the triangulation block with true geocoded station coordinates.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point

TX_LIMITS_URL = (
    "https://reports-public.ieso.ca/public/TxLimitsAllInService0to34Days/"
    "PUB_TxLimitsAllInService0to34Days.xml"
)
OUT_PATH = Path("data/raw/ieso_substations_demo.parquet")


REGION_ANCHORS = {
    "Bruce": (44.32, -81.60),
    "Durham": (43.90, -78.85),
    "Niagara": (43.09, -79.06),
    "Eastern": (44.26, -76.79),
    "Northern": (48.48, -87.30),
    "Northwestern": (48.38, -89.25),
    "Ottawa Valley": (45.42, -75.69),
    "Toronto": (43.65, -79.38),
    "GTA West": (43.58, -79.75),
    "York": (43.88, -79.44),
    "Southwest": (42.98, -81.25),
    "Simcoe": (44.39, -79.69),
    "Central": (44.10, -78.95),
}

# Keyword map used for demo-only region inference from interface names.
REGION_KEYWORDS = {
    "Bruce": ["BRUCE"],
    "Durham": ["DARLINGTON", "PICKERING", "DURHAM"],
    "Niagara": ["QUEENSTON", "NIAGARA", "BECK", "CHIPPAWA", "DECEW"],
    "Eastern": ["KINGSTON", "NAPANEE", "LENOX", "EAST", "OTTAWA"],
    "Northern": ["WAWA", "SUDBURY", "TIMMINS", "NORTH", "MACKAY"],
    "Northwestern": ["DRYDEN", "FORT FRANCES", "KENORA", "THUNDER BAY", "NIPIGON"],
    "Ottawa Valley": ["OTTAWA", "ARNPRIOR", "RENFREW", "PEMBROKE"],
    "Toronto": ["TORONTO", "DOWNTOWN", "LEASIDE"],
    "GTA West": ["MISSISSAUGA", "BRAMPTON", "MILTON", "HALTON"],
    "York": ["YORK", "VAUGHAN", "MARKHAM", "RICHMOND HILL"],
    "Southwest": ["LAMBTON", "WINDSOR", "CHATHAM", "LONDON", "SARNIA"],
    "Simcoe": ["BARRIE", "SIMCOE"],
    "Central": ["PETERBOROUGH", "KAWARTHA", "CENTRAL"],
}


def infer_region(interface_name: str) -> str:
    upper_name = interface_name.upper()
    for region, keywords in REGION_KEYWORDS.items():
        if any(token in upper_name for token in keywords):
            return region
    return "Central"


def clean_name(interface_name: str) -> str:
    # Remove optional [ABBR] suffixes and normalize whitespace.
    name = re.sub(r"\s*\[[^\]]+\]\s*$", "", interface_name).strip()
    return re.sub(r"\s+", " ", name)


def triangulated_point(region: str, idx_in_region: int) -> Point:
    lat0, lon0 = REGION_ANCHORS.get(region, REGION_ANCHORS["Central"])
    tri_angle_deg = [0, 120, 240][idx_in_region % 3]
    ring = (idx_in_region // 3) + 1
    radius_deg = 0.05 * ring  # demo spread around regional anchor

    angle = math.radians(tri_angle_deg)
    lat = lat0 + radius_deg * math.sin(angle)
    lon = lon0 + radius_deg * math.cos(angle)
    return Point(lon, lat)


def fetch_interfaces() -> list[dict]:
    resp = requests.get(TX_LIMITS_URL, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    ns = {"n": root.tag.split("}")[0].strip("{")}

    interfaces = []
    for node in root.findall(".//n:InterfaceData", ns):
        name_node = node.find("n:InterfaceName", ns)
        limit_node = node.find("n:OperatingLimit", ns)
        if name_node is None or not (name_node.text or "").strip():
            continue
        interfaces.append(
            {
                "name": clean_name(name_node.text or ""),
                "operating_limit_mw": float(limit_node.text) if limit_node is not None else None,
            }
        )
    return interfaces


def build_demo_substations() -> gpd.GeoDataFrame:
    interfaces = fetch_interfaces()
    df = pd.DataFrame(interfaces).drop_duplicates(subset=["name"]).reset_index(drop=True)
    df["region"] = df["name"].apply(infer_region)
    df["voltage"] = "230kV"

    # Heuristic demo values for simulation fields expected elsewhere in the app.
    df["capacity_mw"] = df["operating_limit_mw"].fillna(1000).clip(lower=100, upper=5000)
    df["current_load_mw"] = (df["capacity_mw"] * 0.72).round(1)
    df["headroom_mw"] = (df["capacity_mw"] - (df["current_load_mw"] * 1.15)).clip(lower=0).round(1)

    geometry = []
    region_counts: dict[str, int] = {}
    for region in df["region"]:
        idx = region_counts.get(region, 0)
        geometry.append(triangulated_point(region, idx))
        region_counts[region] = idx + 1

    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y
    return gdf


if __name__ == "__main__":
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    demo_subs = build_demo_substations()
    demo_subs.to_parquet(OUT_PATH)
    print(f"Saved {len(demo_subs)} demo IESO substations to {OUT_PATH}")
    print(demo_subs[["name", "region", "capacity_mw"]].head(10).to_string(index=False))
