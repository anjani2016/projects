# pages/7_⚡_IESO_Cache.py
import time
from datetime import datetime

import pandas as pd
import streamlit as st

from energy.ieso_hedging_tool.src.engines import (
    cache_year_ieso,
    generate_synthetic_year_ieso,
    delete_year_cache_ieso,
    load_cache_meta_ieso,
)

st.set_page_config(page_title="IESO Data Cache Manager", layout="wide")

st.title("⚡ IESO Data Cache Manager")
st.caption(
    "Manually fetch and cache historical demand and price (HOEP) data from IESO year-by-year. "
    "Cached data is used by the analytics dashboards."
)

CURRENT_YEAR = datetime.now().year
# IESO public archive goes back reliably to ~2003
ALL_YEARS = list(range(CURRENT_YEAR, 2002, -1))

# ─── Load current cache status ────────────────────────────────────────────────
meta = load_cache_meta_ieso()


def _status_badge(year: int) -> tuple[str, str]:
    """Return (emoji_badge, source_label) for a year."""
    info = meta.get(str(year))
    if info is None:
        return "⬜", "Not cached"
    source = info.get("source", "")
    if source == "ieso_api":
        return "✅", "IESO API"
    return "🟡", "Synthetic (generated)"


def _cached_at(year: int) -> str:
    info = meta.get(str(year))
    if info and "cached_at" in info:
        return info["cached_at"][:16].replace("T", " ")
    return "—"


# ─── Summary metrics ─────────────────────────────────────────────────────────
api_count = sum(1 for y in ALL_YEARS if meta.get(str(y), {}).get("source") == "ieso_api")
syn_count = sum(
    1 for y in ALL_YEARS if meta.get(str(y), {}).get("source") == "synthetic"
)
missing_count = len(ALL_YEARS) - api_count - syn_count

metric_cols = st.columns(4)
with metric_cols[0]:
    st.metric("Total Years", len(ALL_YEARS))
with metric_cols[1]:
    st.metric("✅ Real (IESO)", api_count)
with metric_cols[2]:
    st.metric("🟡 Synthetic", syn_count)
with metric_cols[3]:
    st.metric("⬜ Missing", missing_count)

st.markdown("---")

# ─── Bulk actions ─────────────────────────────────────────────────────────────
st.subheader("Bulk Actions")
bulk_cols = st.columns([1, 1, 1, 2])

with bulk_cols[0]:
    range_start = st.number_input(
        "From Year", min_value=2003, max_value=CURRENT_YEAR,
        value=CURRENT_YEAR - 4, key="bulk_start",
    )
with bulk_cols[1]:
    range_end = st.number_input(
        "To Year", min_value=2003, max_value=CURRENT_YEAR,
        value=CURRENT_YEAR, key="bulk_end",
    )

with bulk_cols[2]:
    st.markdown("<br>", unsafe_allow_html=True)
    fetch_range = st.button(
        "🔄 Fetch Range from IESO", use_container_width=True, type="primary"
    )

with bulk_cols[3]:
    st.markdown("<br>", unsafe_allow_html=True)
    seed_range = st.button(
        "🧪 Generate Synthetic for Range", use_container_width=True
    )

if fetch_range:
    years_to_fetch = list(range(int(range_start), int(range_end) + 1))
    progress_bar = st.progress(0, text="Starting…")
    results = []
    for i, year in enumerate(years_to_fetch):
        progress_bar.progress(
            (i + 1) / len(years_to_fetch),
            text=f"Fetching {year}… ({i + 1}/{len(years_to_fetch)})",
        )
        success, msg = cache_year_ieso(year)
        results.append(msg)
        time.sleep(0.5)  # Delay to be polite to IESO servers
    progress_bar.empty()
    for msg in results:
        if msg.startswith("✅"):
            st.success(msg)
        else:
            st.error(msg)
    st.cache_data.clear()
    st.rerun()

if seed_range:
    years_to_seed = list(range(int(range_start), int(range_end) + 1))
    progress_bar = st.progress(0, text="Generating…")
    for i, year in enumerate(years_to_seed):
        progress_bar.progress(
            (i + 1) / len(years_to_seed),
            text=f"Generating {year}… ({i + 1}/{len(years_to_seed)})",
        )
        generate_synthetic_year_ieso(year)
    progress_bar.empty()
    st.success(
        f"🧪 Generated synthetic data for {years_to_seed[0]}–{years_to_seed[-1]}."
    )
    st.cache_data.clear()
    st.rerun()

st.markdown("---")

# ─── Per-year cache table ─────────────────────────────────────────────────────
st.subheader("Per-Year Cache Status")
st.markdown(
    "**Legend:**  ✅ Real data (IESO)  ·  🟡 Synthetic (generated)  ·  ⬜ Not cached"
)

# Build status dataframe for display
status_rows = []
for year in ALL_YEARS:
    badge, source = _status_badge(year)
    status_rows.append({
        "Year": year,
        "Status": f"{badge} {source}",
        "Cached At": _cached_at(year),
    })
status_df = pd.DataFrame(status_rows)

# Display as a styled table
st.dataframe(
    status_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Year": st.column_config.NumberColumn("Year", format="%d"),
        "Status": st.column_config.TextColumn("Data Source", width="medium"),
        "Cached At": st.column_config.TextColumn("Last Updated", width="medium"),
    },
    height=400,
)

st.markdown("---")

# ─── Individual year actions ──────────────────────────────────────────────────
st.subheader("Single Year Actions")

single_cols = st.columns([1, 1, 1, 1])

with single_cols[0]:
    target_year = st.selectbox("Select Year", options=ALL_YEARS, key="single_yr")

with single_cols[1]:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Fetch from IESO", key="single_fetch", use_container_width=True):
        with st.spinner(f"Fetching {target_year}…"):
            success, msg = cache_year_ieso(target_year)
        if success:
            st.success(msg)
        else:
            st.error(msg)
        st.cache_data.clear()
        time.sleep(1)
        st.rerun()

with single_cols[2]:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🧪 Generate Synthetic", key="single_syn", use_container_width=True):
        generate_synthetic_year_ieso(target_year)
        st.success(f"🧪 Generated synthetic data for {target_year}.")
        st.cache_data.clear()
        time.sleep(1)
        st.rerun()

with single_cols[3]:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Delete Cache", key="single_del", use_container_width=True):
        delete_year_cache_ieso(target_year)
        st.warning(f"🗑️ Deleted cache for {target_year}.")
        st.cache_data.clear()
        time.sleep(1)
        st.rerun()

st.markdown("---")

# ─── Info box ─────────────────────────────────────────────────────────────────
with st.expander("ℹ️ How does caching work?", expanded=False):
    st.markdown(
        """
        ### Cache Architecture

        Grid data is stored as **per-year CSV files** in `data/processed/ieso/`.

        | File | Purpose |
        |------|---------|
        | `ieso_2024.csv` | Hourly Ontario Demand and Price (HOEP) for 2024 |
        | `_cache_meta_ieso.json` | Tracks data source and timestamps |

        ### Data Flow

        ```
        Dashboard loads
            │
            ├─ Year cached? → Read from CSV ✅
            │
            └─ Year missing? → Auto-generate synthetic data 🟡
                               (so the dashboard never breaks)
        ```
        
        Use the **Fetch Range** button above to download real data.
        """
    )
