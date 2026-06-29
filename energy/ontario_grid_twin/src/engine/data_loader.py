import streamlit as st
import pandas as pd
import numpy as np
import os
from energy.ontario_grid_twin.src.engine.grid_model import GridNode
from energy.ontario_grid_twin.src.engine.grid_classifier import add_grid_classification

# ── Category constants ────────────────────────────────────────────────────────
# Ordered list of all generation categories shown in the map sidebar
GENERATION_CATEGORIES = ["Nuclear", "Hydro", "Fossil", "Renewable", "Storage"]

# RGBA colours per category for pydeck layers
GENERATION_CATEGORY_COLORS = {
    "Nuclear":   [255,  70, 180, 220],   # magenta-pink
    "Hydro":     [ 30, 144, 255, 220],   # dodger blue
    "Fossil":    [255, 100,  30, 220],   # orange-red
    "Renewable": [ 50, 205,  50, 220],   # lime green
    "Storage":   [180, 100, 255, 220],   # purple
}

def _normalize_gen(gen) -> 'gpd.GeoDataFrame':
    """
    Ensure 'fuel_type' and 'category' columns are present.
    Older parquet files only have a 'type' column; map those forward.
    """
    # Back-compat: if new columns already exist just return
    if 'fuel_type' not in gen.columns:
        gen['fuel_type'] = gen.get('type', 'Unknown')
    if 'category' not in gen.columns:
        # Derive category from fuel_type for legacy data
        _cat_map = {
            'nuclear': 'Nuclear', 'hydro': 'Hydro',
            'natural gas': 'Fossil', 'gas': 'Fossil', 'oil': 'Fossil',
            'wind': 'Renewable', 'solar': 'Renewable',
            'biofuel': 'Renewable', 'biomass': 'Renewable',
            'battery': 'Storage', 'storage': 'Storage',
        }
        gen['category'] = (
            gen['fuel_type'].str.lower()
            .map(lambda v: next(
                (cat for key, cat in _cat_map.items() if key in v), 'Renewable'
            ))
        )
    # Assign pydeck RGBA colour list per row
    gen['color'] = gen['category'].map(
        lambda c: GENERATION_CATEGORY_COLORS.get(c, [200, 200, 200, 200])
    )
    return gen


@st.cache_data
def load_base_grid():
    """
    Loads substation, line, generation, and existing DC data.
    """
    # Prefer demo IESO-derived substations when present.
    # NOTE: this file can contain triangulated coordinates inferred from region/city
    # names for demonstration only. Replace with clean geocoded substation data when available.
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    demo_subs_path = os.path.join(BASE_DIR, 'data/raw/ieso_substations_demo.parquet')
    subs_path = demo_subs_path if os.path.exists(demo_subs_path) else os.path.join(BASE_DIR, 'data/processed/analyzed_substations.parquet')
    lines_path = os.path.join(BASE_DIR, 'data/raw/ontario_lines.parquet')
    gen_path   = os.path.join(BASE_DIR, 'data/raw/generation_sources.parquet')
    dc_path    = os.path.join(BASE_DIR, 'data/raw/existing_dc.parquet')
    real_demand_path = os.path.join(BASE_DIR, 'data/raw/real_time_demand_centres.parquet')

    import geopandas as gpd
    # Substations
    subs = gpd.read_parquet(subs_path).to_crs(epsg=4326)
    subs['lon'] = subs.geometry.x
    subs['lat']  = subs.geometry.y
    subs = add_grid_classification(subs)

    # Optional files
    lines = gpd.read_parquet(lines_path).to_crs(epsg=4326) if os.path.exists(lines_path) else None

    gen = None
    if os.path.exists(gen_path):
        gen = gpd.read_parquet(gen_path).to_crs(epsg=4326)
        gen['lon'] = gen.geometry.x
        gen['lat']  = gen.geometry.y
        gen = _normalize_gen(gen)

    dc = None
    if os.path.exists(dc_path):
        dc = gpd.read_parquet(dc_path).to_crs(epsg=4326)
        dc['lon'] = dc.geometry.x
        dc['lat']  = dc.geometry.y

    if os.path.exists(real_demand_path):
        real_dc = gpd.read_parquet(real_demand_path).to_crs(epsg=4326)
        real_dc['lon'] = real_dc.geometry.x
        real_dc['lat']  = real_dc.geometry.y
        dc = pd.concat([dc, real_dc], ignore_index=True) if dc is not None else real_dc

    return subs, lines, gen, dc

@st.cache_data
def load_dc_projects():
    """
    Loads Ontario data centre project data (Baxtel or National Observer).
    """
    PROVINCIAL_INTEREST_MW = 6500.0
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    BAXTEL_PATH = os.path.join(BASE_DIR, 'data/raw/baxtel_projects.parquet')

    def categorize_type(mw):
        if pd.isna(mw):      return 'Unknown'
        if mw <= 50:         return 'Mid-Tier (≤50 MW)'
        if mw <= 150:        return 'Large (50–150 MW)'
        return 'Hyperscale (>150 MW)'

    import geopandas as gpd
    if os.path.exists(BAXTEL_PATH):
        try:
            gdf = gpd.read_parquet(BAXTEL_PATH)
            df = pd.DataFrame(gdf.drop(columns='geometry', errors='ignore'))
            for col, default in [('capacity_mw', float('nan')), ('status', 'Identified'),
                                  ('year', 2026), ('region', 'Ontario')]:
                if col not in df.columns:
                    df[col] = default
            df['year'] = df['year'].fillna(2026).astype(int)
            df['capacity_mw'] = pd.to_numeric(df['capacity_mw'], errors='coerce')
            df['Type'] = df['capacity_mw'].apply(categorize_type)
            return df, PROVINCIAL_INTEREST_MW, 'Baxtel'
        except Exception:
            pass

    # Fallback: National Observer
    TOTAL_PROPOSED_CAPACITY_MW = 2202.0
    avg = round((TOTAL_PROPOSED_CAPACITY_MW - 217) / 11, 1)
    
    # Construction of project list (Fixed + Simulated)
    real_projects = [
        {'name': 'Cambridge Data Centre 1',     'capacity_mw': 45.0,  'region': 'Cambridge', 'year': 2026, 'status': 'Proposed'},
        {'name': 'Cambridge Data Centre 2',     'capacity_mw': 45.0,  'region': 'Cambridge', 'year': 2026, 'status': 'Proposed'},
        {'name': 'Microsoft Vaughan Expansion', 'capacity_mw': 100.0, 'region': 'York',      'year': 2026, 'status': 'Under Review'},
        {'name': 'Yondr Toronto',               'capacity_mw': 27.0,  'region': 'Toronto',   'year': 2027, 'status': 'Proposed'}
    ] + [
        {'name': f'Observer Project {i} (Avg)', 'capacity_mw': avg,   'region': 'Various',   'year': 2027 if i<3 else (2028 if i<7 else 2029), 'status': 'Identified'}
        for i in range(1, 12)
    ]
    
    df = pd.DataFrame(real_projects)
    df['Type'] = df['capacity_mw'].apply(categorize_type)
    return df, PROVINCIAL_INTEREST_MW, 'National Observer (Mar 2026)'

def get_grid_nodes(subs):
    """
    Initializes GridNode objects for all substations.
    """
    grid_nodes = {}
    for idx, row in subs.iterrows():
        v_val = 230
        if 'voltage' in row and pd.notnull(row['voltage']):
            try:
                v_val = int(str(row['voltage']).replace('kV', '').strip())
            except ValueError:
                pass
        cap = float(row.get('capacity_mw', 1000))
        b_load = cap - row['headroom_mw'] if 'headroom_mw' in row else float(row.get('current_load_mw', 800))
        grid_nodes[row['name']] = GridNode(name=row['name'], capacity_mw=cap, base_load_mw=b_load, voltage_kv=v_val)
    return grid_nodes
