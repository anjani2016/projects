# pages/1_📊_Market_Data.py
import streamlit as st
import pandas as pd
from energy.ieso_hedging_tool.src.engines.scraper import fetch_ieso_data, save_raw_data
from datetime import datetime

st.title("📊 IESO Market Data Ingestion")
st.markdown("Download and preview historical Hourly Ontario Energy Price (HOEP) data.")

# 1. User Inputs
with st.sidebar:
    st.markdown("**Data Settings**")
    # Improved month selection
    selected_date = st.date_input("Select Month to Scrape", value=datetime(2026, 3, 1), help="Select any day within the month you wish to fetch.")
    year_month = selected_date.strftime("%Y%m")

# 2. Execution Button
if st.button(f"Fetch Data for {selected_date.strftime('%B %Y')}"):
    with st.spinner("Connecting to IESO Servers..."):
        data = fetch_ieso_data(year_month)
        
        if isinstance(data, pd.DataFrame):
            # Save the data to our local structure
            path = save_raw_data(data, year_month)
            
            # Persist data in session state for other pages
            st.session_state['market_data'] = data
            st.session_state['selected_month'] = year_month
            
            st.success(f"Data successfully saved to {path}")
        else:
            st.error(f"Failed to retrieve data: {data}")

st.divider()

# 3. Data Preview & Metrics
if 'market_data' in st.session_state:
    data = st.session_state['market_data']
    
    st.subheader(f"Data Preview for {st.session_state.get('selected_month', '')}")
    
    # 3a. Display Definitions and Timezone
    st.info("""
    **Timezone:** All data is reported in **EST (Eastern Standard Time)** year-round.  
    **LMP (Locational Marginal Price) Components:**
    - **Energy Loss Price:** The cost of electricity lost as heat when moving power through the transmission system.
    - **Energy Congestion Price:** The additional cost when transmission lines reach their limit and more expensive local generation must be used.
    """)

    # 3b. Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Average Price", f"${data['Ontario Price'].mean():.2f}")
    col2.metric("Max Price", f"${data['Ontario Price'].max():.2f}")
    col3.metric("Data Points", len(data))
    
    # 3c. Table Formatting: Reorder columns (Date before Hour)
    # New column order: Date, Hour, Pricing Location, Ontario Price, Energy Loss Price, Energy Congestion Price, Timestamp
    cols = ['Date', 'Hour', 'Pricing Location', 'Ontario Price', 'Energy Loss Price', 'Energy Congestion Price', 'Timestamp']
    # Ensure all columns exist before reordering
    available_cols = [c for c in cols if c in data.columns]
    display_df = data[available_cols]
    
    st.dataframe(display_df, use_container_width=True)
    
    # 3d. Visualization
    st.subheader("Price Trend")
    chart_data = data.set_index('Timestamp')['Ontario Price']
    st.line_chart(chart_data)
else:
    # This shows when the page first loads
    st.info("No data loaded for this session. Use the 'Fetch Data' button in the sidebar to begin.")

st.divider()
st.info("Note: The IESO reports are updated monthly. Ensure you are selecting a period with available public reports.")
