import streamlit as st
import sys
from pathlib import Path

# Ensure src modules can be imported
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.engine.data_loader import load_infrastructure_data
from src.components.map_view import render_dekart_style_map

st.set_page_config(page_title="Affordability Map", page_icon="🗺️", layout="wide")

st.title("🗺️ Affordability & Infrastructure Map")

# Load data
with st.spinner("Loading geospatial data..."):
    df = load_infrastructure_data()

if df.empty:
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Map Filters")

# Filter by Infrastructure Type
infra_types = ["All"] + list(df["infrastructure_type"].unique())
selected_type = st.sidebar.selectbox("Infrastructure Type", infra_types)

# Filter by Affordability Index Range
min_index = float(df["affordability_index"].min())
max_index = float(df["affordability_index"].max())
selected_index_range = st.sidebar.slider(
    "Affordability Index Range", 
    min_value=min_index, 
    max_value=max_index, 
    value=(min_index, max_index),
    step=0.05
)

# Apply Filters
filtered_df = df.copy()

if selected_type != "All":
    filtered_df = filtered_df[filtered_df["infrastructure_type"] == selected_type]

filtered_df = filtered_df[
    (filtered_df["affordability_index"] >= selected_index_range[0]) & 
    (filtered_df["affordability_index"] <= selected_index_range[1])
]

# --- Main Content ---
st.markdown("### 3D Infrastructure Cost Distribution")
st.markdown("The height of the columns represents the **infrastructure cost**, and the color represents the **affordability index** (Green = More Affordable, Red = Less Affordable).")

# Metrics row
col1, col2, col3 = st.columns(3)
col1.metric("Total Cities Displayed", len(filtered_df))
col2.metric("Avg Affordability Index", f"{filtered_df['affordability_index'].mean():.2f}" if not filtered_df.empty else "N/A")
col3.metric("Total Infrastructure Cost", f"${filtered_df['infrastructure_cost'].sum():,.0f}" if not filtered_df.empty else "$0")

# Render Map
st.markdown("---")
render_dekart_style_map(filtered_df)

# Show raw data toggle
if st.checkbox("Show Raw Data"):
    st.dataframe(filtered_df, use_container_width=True)
