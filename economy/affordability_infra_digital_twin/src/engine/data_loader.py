import pandas as pd
import geopandas as gpd
import streamlit as st
from pathlib import Path

@st.cache_data
def load_infrastructure_data() -> pd.DataFrame:
    """
    Loads affordability and infrastructure data from the local CSV.
    In future iterations, this can be swapped out with Snowflake queries.
    """
    data_path = Path("data/sample_infra.csv")
    if not data_path.exists():
        st.error(f"Data file not found: {data_path}")
        return pd.DataFrame()
        
    df = pd.read_csv(data_path)
    
    # Calculate a normalized cost for visualization purposes (e.g. radius size)
    if not df.empty and "infrastructure_cost" in df.columns:
        df["normalized_cost"] = df["infrastructure_cost"] / df["infrastructure_cost"].max()
        
    return df

@st.cache_data
def load_geodata(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    Converts a pandas DataFrame with lat/lon into a GeoDataFrame.
    """
    if df.empty or "latitude" not in df.columns or "longitude" not in df.columns:
        return gpd.GeoDataFrame()
        
    gdf = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"
    )
    return gdf
