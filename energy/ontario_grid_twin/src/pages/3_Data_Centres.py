import streamlit as st
import pandas as pd
import plotly.express as px
from energy.ontario_grid_twin.src.utils.ui_branding import apply_branding

apply_branding()

if 'data_loaded' not in st.session_state:
    st.error("Please return to the [Home Page](../app.py) to initialize the application data.")
    st.stop()

projects = st.session_state['projects']
provincial_interest_mw = st.session_state['provincial_interest_mw']
dc_source = st.session_state['dc_source']

st.markdown("## 🏭 Data Centres")
st.markdown("##### Existing & Projected Ontario Data Centre Portfolio")
st.markdown("<br>", unsafe_allow_html=True)

st.sidebar.header("Filters")
st.sidebar.caption(f"📡 Data source: **{dc_source}**")

regions = sorted(projects['region'].unique())
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)

statuses = sorted(projects['status'].unique())
selected_statuses = st.sidebar.multiselect("Status", statuses, default=statuses)

min_cap, max_cap = int(projects['capacity_mw'].min()), int(projects['capacity_mw'].max())
cap_range = st.sidebar.slider("Capacity Range (MW)", min_cap, max_cap, (min_cap, max_cap))

filtered_df = projects[
    (projects['region'].isin(selected_regions)) &
    (projects['status'].isin(selected_statuses)) &
    (projects['capacity_mw'] >= cap_range[0]) &
    (projects['capacity_mw'] <= cap_range[1])
]

total_proposed = filtered_df['capacity_mw'].sum()
k1, k2, k3 = st.columns(3)
k1.metric("Total Proposed Demand (filtered)", f"{total_proposed:,.0f} MW")
k2.metric("Total Proposed (all projects)", "2,202 MW")
k3.metric("Total Provincial Interest", f"{provincial_interest_mw:,.0f} MW")

if filtered_df.empty:
    st.warning("No projects match the selected filters.")
else:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Data Centre Type")
        dist_df = filtered_df.groupby('Type', observed=False).size().reset_index(name='Count')
        fig_size = px.bar(dist_df, x='Type', y='Count', color='Type',
                          color_discrete_map={'Mid-Tier (≤50 MW)': '#1f77b4', 'Large (50–150 MW)': '#87ceeb', 'Hyperscale (>150 MW)': '#ff3131'})
        fig_size.update_layout(showlegend=False)
        st.plotly_chart(fig_size, use_container_width=True)

    with col2:
        st.subheader("Timeline")
        timeline_df = filtered_df.copy()
        timeline_df['year'] = timeline_df['year'].astype(int).astype(str)
        timeline_df = timeline_df.groupby('year')['capacity_mw'].sum().reset_index()
        fig_time = px.area(timeline_df, x='year', y='capacity_mw', labels={'capacity_mw': 'Projected Capacity (MW)', 'year': 'Year'})
        fig_time.update_xaxes(type='category')
        st.plotly_chart(fig_time, use_container_width=True)

    st.subheader("Project Details")
    st.dataframe(filtered_df[['name','region','capacity_mw','year','status','Type']].rename(columns={'name':'Project','region':'Region','capacity_mw':'Capacity (MW)','year':'Year','status':'Status','Type':'Type'}).sort_values(['Year','Capacity (MW)'], ascending=[True, False]), use_container_width=True)

st.markdown("---")
st.subheader("❄️ Climate-Based Cooling Efficiency")
st.markdown("Ontario's cold climate allows for 'Free Cooling', significantly reducing the energy required for operations.")

region_temps = {'Toronto': 9.2, 'GTA': 8.5, 'York': 7.8, 'Cambridge': 8.1, 'Various': 7.5}
def get_realistic_savings(temp):
    if temp < -10: return 0.70, "Max Free-Cooling Utilization"
    if -10 <= temp < 0: return 0.50, "Compressors Disabled; Fans Only"
    if 0 <= temp < 10: return 0.30, "Partial Evaporative Support"
    return 0.10, "Mechanical Rejection Active"

climate_data = []
for _, row in filtered_df.iterrows():
    avg_t = region_temps.get(row['region'], 7.5)
    savings, note = get_realistic_savings(avg_t)
    effective_pue = 1.0 + (0.30 * (1 - savings)) + 0.08
    climate_data.append({"Project": row['name'], "Region": row['region'], "Avg Annual Temp": f"{avg_t}°C", "Cooling Note": note, "Effective PUE": f"{effective_pue:.2f}", "Savings Factor": f"{savings * 100:.0f}%"})

c1, c2 = st.columns([3, 2])
with c1:
    st.markdown("**Projected Cooling Efficiency by Location**")
    st.table(pd.DataFrame(climate_data))
with c2:
    st.markdown("**Tiered Efficiency Reference**")
    temp_tiers = [{"Range": "-20 to -10°C", "Savings": "70%", "Note": "Max Free-Cooling"}, {"Range": "-10 to 0°C", "Savings": "50%", "Note": "Fans Only"}, {"Range": "0 to 10°C", "Savings": "30%", "Note": "Partial Evaporative"}, {"Range": "10 to 20°C", "Savings": "10%", "Note": "Mechanical Rejection"}]
    st.table(pd.DataFrame(temp_tiers))

st.markdown("---")
st.caption("**Efficiency References:** ASHRAE TC 9.9, M-Cycle Pilot benchmarks.")
st.caption(f"**Data Source:** National Observer (Mar 2026). Total reported: 2,202 MW. Provincial Interest: {provincial_interest_mw} MW.")
