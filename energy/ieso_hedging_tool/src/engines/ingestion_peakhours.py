# src/engines/ingestion_peakhours.py
import logging
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# IESO migrated to reports-public.ieso.ca as part of Market Renewal (2025).
# The current year file is always available at the canonical URL (no year suffix needed).
_BASE_URL = "https://reports-public.ieso.ca/public/RealtimeDemandZonal"
_CURRENT_FILE = "PUB_RealtimeDemandZonal.csv"
_SKIP_ROWS = 3  # Two header rows + one blank before the column row


@st.cache_data(ttl=3600)  # Cache grid telemetry for 1 hour
def fetch_live_ieso_demand() -> pd.DataFrame:
    """
    Pulls the current real-time 5-minute zonal demand from the IESO
    Market Renewal report server and returns a clean hourly DataFrame.

    Source: https://reports-public.ieso.ca/public/RealtimeDemandZonal/
    Report: PUB_RealtimeDemandZonal.csv
    Columns: Date, Hour, Interval (1-12), Ontario Demand, [10 zones], Zones Total, DIFF

    Returns columns: Timestamp, Date, Hour, Ontario Demand
    """
    url = f"{_BASE_URL}/{_CURRENT_FILE}"
    logger.info("Fetching IESO real-time demand from: %s", url)

    try:
        df = pd.read_csv(url, skiprows=_SKIP_ROWS)

        # Drop any trailing metadata rows that lack Date/Hour
        df = df.dropna(subset=["Date", "Hour"])

        # Enforce types — values arrive with leading whitespace from fixed-width formatting
        df["Hour"] = pd.to_numeric(df["Hour"], errors="coerce").astype("Int64")
        df["Ontario Demand"] = pd.to_numeric(df["Ontario Demand"], errors="coerce")
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        df = df.dropna(subset=["Date", "Hour", "Ontario Demand"])

        # The report is 5-minute (12 intervals per hour).
        # Aggregate to hourly max demand — this is what the analytics page expects.
        df_hourly = (
            df.groupby(["Date", "Hour"], as_index=False)["Ontario Demand"]
            .max()
        )

        # Build a localized Timestamp (Hour 1 → 00:00, Hour 24 → 23:00)
        df_hourly["Timestamp"] = df_hourly["Date"] + pd.to_timedelta(
            df_hourly["Hour"] - 1, unit="h"
        )

        result = df_hourly[["Timestamp", "Date", "Hour", "Ontario Demand"]].copy()
        result["Date"] = result["Date"].dt.strftime("%Y-%m-%d")

        logger.info(
            "IESO demand fetch complete — %d hourly rows from %s to %s",
            len(result),
            result["Timestamp"].min(),
            result["Timestamp"].max(),
        )
        return result

    except Exception as e:
        logger.error("IESO Ingestion Pipeline Error: %s", e, exc_info=True)
        st.error(f"IESO Ingestion Pipeline Error: {e}")
        return pd.DataFrame()