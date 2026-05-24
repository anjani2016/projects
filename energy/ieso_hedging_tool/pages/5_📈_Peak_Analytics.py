# pages/5_📈_Peak_Analytics.py
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

from energy.ieso_hedging_tool.src.engines import fetch_historical_grid_matrix, fetch_multi_year_weather, fetch_daily_weather, load_cache_meta

st.set_page_config(page_title="H-PHA Macro Analysis", layout="wide")

st.title("Grid Peak & Financial Pricing Analytics Dashboard")
st.caption(
    "Correlating Regional Climate Patterns, IESO Monthly Coincident Peaks, "
    "and Market Price Structural Shifts"
)

MONTHS_MAP = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}
CURRENT_YEAR = datetime.now().year

# ==============================================================================
# SIDEBAR — GLOBAL YEAR RANGE SELECTOR
# ==============================================================================
st.sidebar.header("📅 Historical Range")
st.sidebar.markdown("Select specific years for temperature and demand data analysis.")

all_years = list(range(CURRENT_YEAR, 1995, -1))

if "selected_years" not in st.session_state:
    st.session_state["selected_years"] = list(range(CURRENT_YEAR, CURRENT_YEAR - 6, -1))

selected_years = st.sidebar.multiselect(
    "Selected Years",
    options=all_years,
    default=st.session_state["selected_years"],
    help="Select multiple individual years from 1996 to current year for analysis.",
)

st.session_state["selected_years"] = selected_years

if not selected_years:
    st.sidebar.warning("Please select at least one year.")
    st.stop()

start_year = min(selected_years)
end_year = max(selected_years)

st.sidebar.markdown(f"**Selected:** {len(selected_years)} years")

# Quick-preset buttons
st.sidebar.markdown("**Quick Presets:**")
preset_cols = st.sidebar.columns(3)
with preset_cols[0]:
    if st.button("5 yr", use_container_width=True):
        st.session_state["selected_years"] = list(range(CURRENT_YEAR, CURRENT_YEAR - 5, -1))
        st.rerun()
with preset_cols[1]:
    if st.button("10 yr", use_container_width=True):
        st.session_state["selected_years"] = list(range(CURRENT_YEAR, CURRENT_YEAR - 10, -1))
        st.rerun()
with preset_cols[2]:
    if st.button("30 yr", use_container_width=True):
        st.session_state["selected_years"] = list(range(CURRENT_YEAR, CURRENT_YEAR - 30, -1))
        st.rerun()

# ==============================================================================
# DATA LOADING
# ==============================================================================
with st.spinner("Loading grid and weather data…"):
    grid_df = fetch_historical_grid_matrix(start_year=start_year, end_year=end_year)
    weather_df = fetch_multi_year_weather(start_year=start_year, end_year=end_year)
    
    # Filter to only the selected years
    grid_df = grid_df[grid_df["Year"].isin(selected_years)]
    weather_df = weather_df[weather_df["Year"].astype(int).isin(selected_years)]

available_years = sorted(grid_df["Year"].unique()) if not grid_df.empty else []

# ─── Weather data source indicator ────────────────────────────────────────────
cache_meta = load_cache_meta()
_real_sources = {"environment_canada", "open_meteo", "api"}
real_years = []
synthetic_years = []
missing_years = []
for y in selected_years:
    info = cache_meta.get(str(y))
    if info is None:
        missing_years.append(y)
    elif info.get("source") in _real_sources:
        real_years.append(y)
    else:
        synthetic_years.append(y)

if real_years and not synthetic_years and not missing_years:
    st.success(
        f"✅ **Weather data:** All {len(real_years)} years use real observed data."
    )
elif synthetic_years or missing_years:
    syn_label = f"{len(synthetic_years)} synthetic" if synthetic_years else ""
    real_label = f"{len(real_years)} real" if real_years else ""
    parts = [p for p in [real_label, syn_label] if p]
    st.warning(
        f"⚠️ **Weather data:** {', '.join(parts)}. "
        f"Go to **🌡️ Weather Cache** page to fetch real data from Environment Canada."
    )

# ==============================================================================
# ROW 1: TEMPERATURE CLIMATOLOGY + PEAK DEMAND BY MONTH
# ==============================================================================
col1, col2 = st.columns([1, 1], gap="large")

# --- 1a. Year-Over-Year Weekly Temperature Profile ---
with col1:
    st.subheader("1. Year-Over-Year Weekly Temperature Profile")
    st.markdown(
        "Macro environmental assessment identifying systemic winter heating and summer "
        "cooling inflection vectors across the GTA corridor."
    )

    if not weather_df.empty:
        # Let users pick which years to overlay on the temperature chart
        weather_years = sorted(weather_df["Year"].unique())
        selected_temp_years = st.multiselect(
            "Overlay Years:",
            options=weather_years,
            default=weather_years[-3:] if len(weather_years) >= 3 else weather_years,
            key="temp_yr_sel",
        )

        filtered_weather = weather_df[weather_df["Year"].isin(selected_temp_years)]

        if not filtered_weather.empty:
            fig_temp = px.line(
                filtered_weather,
                x="Week",
                y="Temperature",
                color="Year",
                title="Average Weekly Ambient Temperature Baseline",
                labels={
                    "Temperature": "Mean Temperature (°C)",
                    "Week": "ISO Week of Year",
                },
                template="plotly_dark",
            )
            fig_temp.update_layout(
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_temp, use_container_width=True)
        else:
            st.info("Select at least one year to display the temperature profile.")
    else:
        st.warning("Weather data is unavailable.")

# --- 1b. Multi-Year Monthly Coincident Peaks ---
with col2:
    st.subheader("2. Multi-Year Monthly Coincident Peaks")
    st.markdown(
        "Isolate and evaluate peak load configurations by selecting specific "
        "historical operational cycles."
    )

    selected_peak_years = st.multiselect(
        "Filter Analysis Years:",
        options=available_years,
        default=available_years[-3:] if len(available_years) >= 3 else available_years,
        key="peak_yr_sel",
    )

    if selected_peak_years:
        filtered_grid = grid_df[grid_df["Year"].isin(selected_peak_years)].copy()

        monthly_peaks = (
            filtered_grid.groupby(["Year", "Month"])["Ontario Demand"]
            .max()
            .reset_index()
        )
        monthly_peaks["Month Name"] = monthly_peaks["Month"].map(MONTHS_MAP)
        monthly_peaks["Year"] = monthly_peaks["Year"].astype(str)
        
        monthly_avgs = (
            filtered_grid.groupby(["Year", "Month"])["Ontario Demand"]
            .mean()
            .reset_index()
        )
        monthly_avgs["Month Name"] = monthly_avgs["Month"].map(MONTHS_MAP)
        monthly_avgs["Year"] = monthly_avgs["Year"].astype(str)

        fig_peaks = px.line(
            monthly_peaks,
            x="Month Name",
            y="Ontario Demand",
            color="Year",
            title="Maximum Coincident Peak Demand Profile by Month",
            labels={
                "Ontario Demand": "Peak Demand (MW)",
                "Month Name": "Operational Month",
            },
            category_orders={"Month Name": list(MONTHS_MAP.values())},
            template="plotly_dark",
            markers=True,
        )
        fig_peaks.update_layout(
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        
        fig_avgs = px.line(
            monthly_avgs,
            x="Month Name",
            y="Ontario Demand",
            color="Year",
            title="Average Monthly Demand Profile",
            labels={
                "Ontario Demand": "Average Demand (MW)",
                "Month Name": "Operational Month",
            },
            category_orders={"Month Name": list(MONTHS_MAP.values())},
            template="plotly_dark",
            markers=True,
        )
        fig_avgs.update_layout(
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        
        tab1, tab2 = st.tabs(["🔥 Peak Demand", "📊 Average Demand"])
        with tab1:
            st.plotly_chart(fig_peaks, use_container_width=True)
        with tab2:
            st.plotly_chart(fig_avgs, use_container_width=True)
    else:
        st.info(
            "Select at least one analysis year to generate the coincident peak profile."
        )

st.markdown("---")

# ==============================================================================
# ROW 2: TEMPERATURE ↔ PEAK DEMAND CORRELATION
# ==============================================================================
st.subheader("3. Temperature–Demand Correlation Analysis")
st.markdown(
    "Quantify the relationship between ambient temperature and peak grid demand. "
    "High correlations in the tails (extreme cold / extreme heat) signal "
    "temperature-driven hedging exposure windows."
)

if not weather_df.empty and not grid_df.empty:
    # Build a merged monthly dataset: average temp + peak demand per month/year
    # Weather: weekly → monthly average
    weather_monthly = weather_df.copy()
    weather_monthly["Year"] = weather_monthly["Year"].astype(int)
    # Map ISO week to approximate month (week 1-4 ≈ Jan, etc.)
    weather_monthly["Month"] = ((weather_monthly["Week"] - 1) // 4.33 + 1).clip(
        upper=12
    ).astype(int)
    weather_monthly_avg = (
        weather_monthly.groupby(["Year", "Month"])["Temperature"]
        .mean()
        .reset_index()
        .rename(columns={"Temperature": "Avg Temp (°C)"})
    )

    # Demand: monthly peak
    demand_monthly = (
        grid_df.groupby(["Year", "Month"])["Ontario Demand"]
        .max()
        .reset_index()
        .rename(columns={"Ontario Demand": "Peak Demand (MW)"})
    )

    # Average Demand: monthly mean
    demand_monthly_avg = (
        grid_df.groupby(["Year", "Month"])["Ontario Demand"]
        .mean()
        .reset_index()
        .rename(columns={"Ontario Demand": "Average Demand (MW)"})
    )

    # Merge
    corr_df = pd.merge(weather_monthly_avg, demand_monthly, on=["Year", "Month"], how="inner")
    corr_df = pd.merge(corr_df, demand_monthly_avg, on=["Year", "Month"], how="inner")
    corr_df["Month Name"] = corr_df["Month"].map(MONTHS_MAP)
    corr_df["Year"] = corr_df["Year"].astype(str)

    corr_col1, corr_col2 = st.columns([3, 2], gap="large")

    with corr_col1:
        # Scatter with trendline (Peak)
        fig_corr_peak = px.scatter(
            corr_df,
            x="Avg Temp (°C)",
            y="Peak Demand (MW)",
            color="Year",
            hover_data=["Month Name"],
            trendline="ols",
            title="Monthly Peak Demand vs. Average Temperature",
            template="plotly_dark",
        )
        fig_corr_peak.update_traces(marker=dict(size=8, opacity=0.8))
        fig_corr_peak.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
        
        # Scatter with trendline (Average)
        fig_corr_avg = px.scatter(
            corr_df,
            x="Avg Temp (°C)",
            y="Average Demand (MW)",
            color="Year",
            hover_data=["Month Name"],
            trendline="ols",
            title="Monthly Average Demand vs. Average Temperature",
            template="plotly_dark",
        )
        fig_corr_avg.update_traces(marker=dict(size=8, opacity=0.8))
        fig_corr_avg.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
        
        corr_tab1, corr_tab2 = st.tabs(["🔥 Peak vs Temp", "📊 Average vs Temp"])
        with corr_tab1:
            st.plotly_chart(fig_corr_peak, use_container_width=True)
        with corr_tab2:
            st.plotly_chart(fig_corr_avg, use_container_width=True)

    with corr_col2:
        # Correlation heatmap by month
        pivot = corr_df.pivot_table(
            index="Month Name",
            columns="Year",
            values="Peak Demand (MW)",
            aggfunc="max",
        )
        # Reorder months
        month_order = [m for m in MONTHS_MAP.values() if m in pivot.index]
        pivot = pivot.reindex(month_order)

        fig_heat = px.imshow(
            pivot,
            title="Peak Demand Heatmap (MW) by Month × Year",
            labels=dict(x="Year", y="Month", color="Peak MW"),
            color_continuous_scale="YlOrRd",
            aspect="auto",
            template="plotly_dark",
        )
        fig_heat.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    # Summary statistics
    st.markdown("#### 📊 Statistical Summary")
    r_value = corr_df["Avg Temp (°C)"].corr(corr_df["Peak Demand (MW)"])
    stat_cols = st.columns(4)
    with stat_cols[0]:
        st.metric("Pearson r", f"{r_value:.3f}")
    with stat_cols[1]:
        st.metric("R²", f"{r_value**2:.3f}")
    with stat_cols[2]:
        st.metric(
            "Hottest Month Peak",
            f"{corr_df.loc[corr_df['Avg Temp (°C)'].idxmax(), 'Peak Demand (MW)']:,.0f} MW",
        )
    with stat_cols[3]:
        st.metric(
            "Coldest Month Peak",
            f"{corr_df.loc[corr_df['Avg Temp (°C)'].idxmin(), 'Peak Demand (MW)']:,.0f} MW",
        )
else:
    st.warning("Insufficient data to compute temperature–demand correlation.")

st.markdown("---")

# ==============================================================================
# ROW 3: DUAL-AXIS OVERLAY — Temperature & Demand on Shared Timeline
# ==============================================================================
st.subheader("4. Dual-Axis Overlay: Temperature & Peak Demand Timeline")
st.markdown(
    "Visualize temperature and demand trajectories on a shared timeline to "
    "identify coincident extremes and lagged response patterns."
)

if not weather_df.empty and not grid_df.empty:
    # Build weekly demand peaks to align with weekly temperature
    grid_weekly = grid_df.copy()
    grid_weekly["Week"] = grid_weekly["Timestamp"].dt.isocalendar().week.astype(int)
    grid_weekly["Year_str"] = grid_weekly["Year"].astype(str)

    weekly_demand = (
        grid_weekly.groupby(["Year_str", "Week"])["Ontario Demand"]
        .max()
        .reset_index()
        .rename(columns={"Year_str": "Year", "Ontario Demand": "Peak Demand (MW)"})
    )

    weekly_demand_avg = (
        grid_weekly.groupby(["Year_str", "Week"])["Ontario Demand"]
        .mean()
        .reset_index()
        .rename(columns={"Year_str": "Year", "Ontario Demand": "Average Demand (MW)"})
    )

    # Let user pick a single year for the overlay
    overlay_years = sorted(weather_df["Year"].unique())
    overlay_year = st.selectbox(
        "Select Year for Overlay:",
        options=overlay_years,
        index=len(overlay_years) - 1,
        key="overlay_yr_sel",
    )

    temp_yr = weather_df[weather_df["Year"] == overlay_year]
    demand_yr = weekly_demand[weekly_demand["Year"] == overlay_year]
    demand_avg_yr = weekly_demand_avg[weekly_demand_avg["Year"] == overlay_year]

    if not temp_yr.empty and not demand_yr.empty:
        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])

        fig_dual.add_trace(
            go.Scatter(
                x=temp_yr["Week"],
                y=temp_yr["Temperature"],
                name="Avg Temp (°C)",
                mode="lines+markers",
                marker=dict(size=4),
                line=dict(color="#00d4ff", width=2),
            ),
            secondary_y=False,
        )
        fig_dual.add_trace(
            go.Scatter(
                x=demand_yr["Week"],
                y=demand_yr["Peak Demand (MW)"],
                name="Peak Demand (MW)",
                mode="lines+markers",
                marker=dict(size=4),
                line=dict(color="#ff6b6b", width=2),
            ),
            secondary_y=True,
        )
        fig_dual.add_trace(
            go.Scatter(
                x=demand_avg_yr["Week"],
                y=demand_avg_yr["Average Demand (MW)"],
                name="Average Demand (MW)",
                mode="lines",
                line=dict(color="#ffc071", width=2, dash="dash"),
            ),
            secondary_y=True,
        )

        fig_dual.update_layout(
            title=f"Weekly Temperature vs. Peak Demand — {overlay_year}",
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1
            ),
            hovermode="x unified",
        )
        fig_dual.update_xaxes(title_text="ISO Week of Year")
        fig_dual.update_yaxes(title_text="Avg Temperature (°C)", secondary_y=False)
        fig_dual.update_yaxes(title_text="Demand (MW)", secondary_y=True)

        st.plotly_chart(fig_dual, use_container_width=True)

        st.caption(
            "💡 **Insight:** U-shaped demand curves (high demand at both temperature "
            "extremes) indicate dual heating/cooling exposure — a critical factor for "
            "seasonal hedging strategy design."
        )
    else:
        st.info(f"No aligned data available for {overlay_year}.")
else:
    st.warning("Insufficient data for the dual-axis overlay.")

st.markdown("---")

# ==============================================================================
# ROW 4: WHOLESALE PRICING REGIME ANALYSIS
# ==============================================================================
st.subheader("5. Wholesale Pricing Discovery Panel: HOEP & LMP Market Evolution")
st.markdown(
    "Analyze weekly settlement averages across the market transition. "
    "Data switches dynamically from the legacy **Hourly Ontario Energy Price (HOEP)** "
    "to **Locational Marginal Pricing (LMP)** structures."
)

ctrl_col1, ctrl_col2 = st.columns(2)
with ctrl_col1:
    selected_price_years = st.multiselect(
        "Target Settlement Years:",
        options=available_years,
        default=[y for y in [2024, 2025] if y in available_years],
        key="price_yr_sel",
    )
with ctrl_col2:
    selected_price_months = st.multiselect(
        "Target Seasonal Months:",
        options=list(MONTHS_MAP.keys()),
        default=[6, 7, 8],
        format_func=lambda x: MONTHS_MAP[x],
        key="price_mo_sel",
    )

if selected_price_years and selected_price_months:
    price_mask = grid_df["Year"].isin(selected_price_years) & grid_df["Month"].isin(
        selected_price_months
    )
    price_filtered = grid_df[price_mask].copy()

    price_filtered["Week"] = price_filtered["Timestamp"].dt.isocalendar().week

    weekly_prices = (
        price_filtered.groupby(["Year", "Week", "Price_Type"])["Market_Price"]
        .mean()
        .reset_index()
    )
    weekly_prices["Year & Regime"] = (
        weekly_prices["Year"].astype(str) + " – " + weekly_prices["Price_Type"]
    )

    fig_price = px.line(
        weekly_prices,
        x="Week",
        y="Market_Price",
        color="Year & Regime",
        title="Average Weekly Wholesale Settlement Profiles",
        labels={
            "Market_Price": "Wholesale Price ($/MWh)",
            "Week": "ISO Week of Year",
        },
        template="plotly_dark",
        markers=True,
    )
    fig_price.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_price, use_container_width=True)

    st.caption(
        "💡 **Market Design Note:** Notice the pricing volatility footprint shifts "
        "after May 2025. LMP frameworks reflect localized transmission congestion and "
        "marginal losses, unlike the single province-wide pool pricing utilized by legacy HOEP."
    )
else:
    st.info(
        "Select a valid combination of years and operational months to display the pricing timeline."
    )

st.markdown("---")

# ==============================================================================
# ROW 5: TOP 5 PEAK HOURS HEATMAP (5CP)
# ==============================================================================
st.subheader("6. Top 5 Peak Hours Heatmap (5CP Analysis)")
st.markdown(
    "Identify the concentration of the top 5 highest daily peak hours per year. "
    "These coincident peaks are critical for Global Adjustment (GA) cost allocation and targeted load curtailment."
)

heatmap_years = st.multiselect(
    "Select Years for 5CP Analysis:",
    options=available_years,
    default=available_years[-5:] if len(available_years) >= 5 else available_years,
    key="heatmap_yr_sel",
)

if heatmap_years and not grid_df.empty:
    heatmap_grid = grid_df[grid_df["Year"].isin(heatmap_years)].copy()
    heatmap_grid["Date"] = heatmap_grid["Timestamp"].dt.date
    
    # 1. Find the daily max demand hour for each day
    heatmap_grid = heatmap_grid.sort_values("Ontario Demand", ascending=False)
    daily_peaks = heatmap_grid.drop_duplicates(subset=["Year", "Date"])
    
    # 2. Get top 5 days per year
    top5_per_year = daily_peaks.groupby("Year").head(5)
    
    # 3. Create a 2D histogram / heatmap of Month vs Hour
    top5_per_year["Month Name"] = top5_per_year["Month"].map(MONTHS_MAP)
    
    heatmap_matrix = pd.crosstab(
        index=top5_per_year["Hour"], 
        columns=top5_per_year["Month Name"]
    )
    
    # Reindex to ensure all 24 hours and 12 months are present
    month_order = list(MONTHS_MAP.values())
    heatmap_matrix = heatmap_matrix.reindex(index=range(1, 25), columns=month_order, fill_value=0)
    
    year_range_str = f"{min(heatmap_years)} - {max(heatmap_years)}" if len(heatmap_years) > 1 else str(heatmap_years[0])
    
    fig_5cp = px.imshow(
        heatmap_matrix,
        title=f"Frequency of Top 5 Annual Peaks by Month and Hour ({year_range_str})",
        labels=dict(x="Month", y="Hour of Day", color="Peak Frequency"),
        color_continuous_scale="YlOrRd",
        aspect="auto",
        template="plotly_dark",
    )
    fig_5cp.update_yaxes(autorange="reversed", tickmode="linear", tick0=1, dtick=1) 
    fig_5cp.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_5cp, use_container_width=True)
    
    # --- Daily Temperature Correlation ---
    daily_weather = fetch_daily_weather(int(min(heatmap_years)), int(max(heatmap_years)))
    if not daily_weather.empty:
        top5_per_year = pd.merge(
            top5_per_year, 
            daily_weather[["Date", "Temperature"]].rename(columns={"Temperature": "Daily Temp (°C)"}), 
            on="Date", 
            how="left"
        )
        
        fig_temp_scatter = px.scatter(
            top5_per_year,
            x="Daily Temp (°C)",
            y="Ontario Demand",
            color="Year",
            size="Ontario Demand",
            hover_data=["Date", "Hour"],
            title=f"5CP Peak Demand vs. Daily Average Temperature",
            template="plotly_dark",
            trendline="ols" if len(top5_per_year.dropna(subset=["Daily Temp (°C)"])) > 2 else None
        )
        fig_temp_scatter.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_temp_scatter, use_container_width=True)
    
    with st.expander("Show Top 5 Peak Records Data"):
        display_cols = ["Year", "Date", "Hour", "Ontario Demand"]
        if "Daily Temp (°C)" in top5_per_year.columns:
            display_cols.append("Daily Temp (°C)")
            
        st.dataframe(
            top5_per_year[display_cols]
            .sort_values(["Year", "Ontario Demand"], ascending=[False, False])
            .reset_index(drop=True),
            use_container_width=True
        )
else:
    st.info("Select at least one year to generate the 5CP heatmap.")

st.markdown("---")

# ==============================================================================
# ROW 6: TOP PEAK HOURS RISK HEATMAP (BASE PERIOD)
# ==============================================================================
st.subheader("7. Top Peak Hours Risk Heatmap (Base Period Grid)")
st.markdown(
    "Aggregate the absolute peak hours of each year across a continuous **Base Period (May 1 to April 30)** calendar. "
    "Hours are scored by rank (e.g., Rank 1 = Max Points, Lowest Rank = 1 pt). High-intensity clusters reveal "
    "the most statistically dangerous days and hours for peak exposure across multiple years."
)

risk_col1, risk_col2 = st.columns([2, 1])
with risk_col1:
    risk_years = st.multiselect(
        "Select Years for Base Period Risk Analysis:",
        options=available_years,
        default=available_years[-5:] if len(available_years) >= 5 else available_years,
        key="risk_yr_sel",
    )
with risk_col2:
    top_n_hours = st.slider(
        "Top Hours per Year (1-100):",
        min_value=1,
        max_value=100,
        value=50,
        step=1,
        key="risk_top_n"
    )

if risk_years and not grid_df.empty:
    risk_grid = grid_df[grid_df["Year"].isin(risk_years)].copy()
    
    # Extract top N hours per year dynamically
    def get_top_n(group):
        top_n = group.nlargest(top_n_hours, 'Ontario Demand').copy()
        top_n['Rank'] = range(1, len(top_n) + 1)
        top_n['Score'] = (top_n_hours + 1) - top_n['Rank']
        return top_n
    
    topn_df = risk_grid.groupby("Year", group_keys=False).apply(get_top_n)
    
    # Map to Base Period Day (1 = May 1, 366 = Apr 30 leap)
    import datetime
    base_dates = [datetime.datetime(2023, 5, 1) + datetime.timedelta(days=i) for i in range(366)]
    date_to_bp = { (d.month, d.day): i+1 for i, d in enumerate(base_dates) }
    bp_to_label = { i+1: d.strftime('%b %d') for i, d in enumerate(base_dates) }
    
    topn_df['BP_Day'] = topn_df['Timestamp'].apply(lambda x: date_to_bp[(x.month, x.day)])
    
    # Aggregate scores by BP_Day and Hour
    risk_agg = topn_df.groupby(["BP_Day", "Hour"])["Score"].sum().reset_index()
    
    # Pivot to 24 (Hour) x 366 (BP_Day) matrix
    risk_matrix = risk_agg.pivot(index="Hour", columns="BP_Day", values="Score").fillna(0)
    risk_matrix = risk_matrix.reindex(index=range(1, 25), columns=range(1, 367), fill_value=0)
    
    # Crop empty tails
    valid_cols = risk_matrix.columns[risk_matrix.sum(axis=0) > 0]
    if len(valid_cols) > 0:
        min_col = valid_cols.min()
        max_col = valid_cols.max()
        risk_matrix = risk_matrix.loc[:, min_col:max_col]
        day_labels = [bp_to_label[c] for c in risk_matrix.columns]
    else:
        day_labels = [bp_to_label[c] for c in risk_matrix.columns]
    
    import plotly.graph_objects as go
    
    year_range_str = f"{min(risk_years)} - {max(risk_years)}" if len(risk_years) > 1 else str(risk_years[0])
    
    fig_risk = go.Figure(data=go.Heatmap(
        z=risk_matrix.values,
        x=day_labels,
        y=list(range(1, 25)),
        colorscale="Inferno",
        hoverongaps=False,
        hovertemplate="<b>Date:</b> %{x}<br><b>Hour:</b> %{y}<br><b>Risk Score:</b> %{z}<extra></extra>"
    ))
    
    fig_risk.update_layout(
        title=f"Top {top_n_hours} Peak Hours Risk Concentration ({year_range_str})",
        xaxis_title="Base Period (May 1 - Apr 30)",
        yaxis_title="Hour of Day",
        yaxis=dict(autorange="reversed", tickmode="linear", tick0=1, dtick=1),
        xaxis=dict(tickangle=45, nticks=24),
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=500
    )
    
    st.plotly_chart(fig_risk, use_container_width=True)
else:
    st.info("Select at least one year to generate the Risk Heatmap.")