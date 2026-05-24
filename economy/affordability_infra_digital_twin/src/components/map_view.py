import pandas as pd
import pydeck as pdk
import streamlit as st

def render_dekart_style_map(df: pd.DataFrame):
    """
    Renders a 3D interactive Pydeck map (similar to Kepler.gl/Dekart) 
    using the provided DataFrame.
    """
    if df.empty:
        st.warning("No data available to display on the map.")
        return

    # Define color scale based on affordability index
    # (Lower affordability = red, higher = green)
    def get_color(index):
        if index < 0.5:
            return [220, 50, 50, 200]  # Red for less affordable
        elif index < 0.7:
            return [255, 200, 0, 200]  # Yellow/Orange for medium
        else:
            return [50, 200, 50, 200]  # Green for more affordable

    # We apply the color logic. In a larger dataset, we might vectorize this.
    df["color"] = df["affordability_index"].apply(get_color)
    
    # Calculate radius for points based on population
    df["radius"] = df["population"] / 100

    # 1. 3D Column Layer for Infrastructure Cost
    column_layer = pdk.Layer(
        "ColumnLayer",
        data=df,
        get_position=["longitude", "latitude"],
        get_elevation="infrastructure_cost",
        elevation_scale=0.05,
        radius=3000,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
    )
    
    # 2. Scatterplot Layer for Population base
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["longitude", "latitude"],
        get_radius="radius",
        get_fill_color=[100, 150, 250, 100],
        pickable=True
    )

    # Calculate viewport center based on data
    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()

    # Define initial view state
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=6.5,
        pitch=45,
        bearing=0
    )

    # Render the pydeck chart
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v10",
        initial_view_state=view_state,
        layers=[scatter_layer, column_layer],
        tooltip={
            "html": "<b>City:</b> {city} <br/>"
                    "<b>Type:</b> {infrastructure_type} <br/>"
                    "<b>Cost:</b> ${infrastructure_cost} <br/>"
                    "<b>Affordability Index:</b> {affordability_index}",
            "style": {"backgroundColor": "steelblue", "color": "white"}
        }
    ))
