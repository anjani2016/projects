import streamlit as st

# Configure the Streamlit application
st.set_page_config(
    page_title="Affordability Infra Digital Twin",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

def main():
    st.title("🏙️ Affordability Infra Digital Twin")
    
    st.markdown("""
    Welcome to the **Affordability Infrastructure Digital Twin**. 
    
    This platform provides high-performance, interactive visualizations of infrastructure costs
    and their correlation with affordability indices across various regions.
    
    ### How to use this tool:
    1. Navigate to the **Affordability Map** page from the sidebar to interact with the 3D map.
    2. Use the filters to slice data by infrastructure type and affordability index.
    3. Hover over the 3D columns to view detailed metrics for each city.
    
    *Note: This current iteration runs on local CSV data using Pydeck for geospatial mapping. 
    Future iterations will integrate directly with Snowflake for large-scale data modeling.*
    """)
    
    st.info("👈 Select a page from the sidebar to get started!")
    
    st.markdown("---")
    st.caption("Powered by Streamlit, Pydeck, and Pandas")

if __name__ == "__main__":
    main()
