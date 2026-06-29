# pages/6_🌡️_Weather_Cache.py
import time
from datetime import datetime

import pandas as pd
import streamlit as st

from energy.ieso_hedging_tool.src.engines import (
    cache_year,
    generate_synthetic_year,
    delete_year_cache,
    load_cache_meta,
)

st.set_page_config(page_title="Weather Data Cache Manager", layout="wide")

st.title("🌡️ Weather Data Cache Manager")
st.caption(
    "Manually fetch and cache historical weather data from Environment Canada (primary) "
    "or Open-Meteo (fallback). Cached data is used by the Peak Analytics dashboard."
)

CURRENT_YEAR = datetime.now().year
ALL_YEARS = list(range(CURRENT_YEAR, CURRENT_YEAR - 31, -1))  # newest first

# ─── Load current cache status ────────────────────────────────────────────────
meta = load_cache_meta()


def _status_badge(year: int) -> tuple[str, str]:
    """Return (emoji_badge, source_label) for a year."""
    info = meta.get(str(year))
    if info is None:
        return "⬜", "Not cached"
    source = info.get("source", "")
    if source == "environment_canada":
        return "✅", "Environment Canada"
    if source == "open_meteo":
        return "✅", "Open-Meteo"
    if source == "api":
        return "✅", "API (real data)"
    return "🟡", "Synthetic (generated)"


def _cached_at(year: int) -> str:
    info = meta.get(str(year))
    if info and "cached_at" in info:
        return info["cached_at"][:16].replace("T", " ")
    return "—"


# ─── Summary metrics ─────────────────────────────────────────────────────────
real_sources = {"environment_canada", "open_meteo", "api"}
api_count = sum(1 for y in ALL_YEARS if meta.get(str(y), {}).get("source") in real_sources)
syn_count = sum(
    1 for y in ALL_YEARS if meta.get(str(y), {}).get("source") == "synthetic"
)
missing_count = len(ALL_YEARS) - api_count - syn_count

metric_cols = st.columns(4)
with metric_cols[0]:
    st.metric("Total Years", len(ALL_YEARS))
with metric_cols[1]:
    st.metric("✅ Real (API)", api_count)
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
        "From Year", min_value=CURRENT_YEAR - 30, max_value=CURRENT_YEAR,
        value=CURRENT_YEAR - 4, key="bulk_start",
    )
with bulk_cols[1]:
    range_end = st.number_input(
        "To Year", min_value=CURRENT_YEAR - 30, max_value=CURRENT_YEAR,
        value=CURRENT_YEAR, key="bulk_end",
    )

with bulk_cols[2]:
    st.markdown("<br>", unsafe_allow_html=True)
    fetch_range = st.button(
        "🔄 Fetch Range from API", use_container_width=True, type="primary"
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
        success, msg = cache_year(year)
        results.append(msg)
        time.sleep(0.3)  # Small delay to be polite to the API
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
        generate_synthetic_year(year)
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
    "**Legend:**  ✅ Real data (Environment Canada / Open-Meteo)  ·  🟡 Synthetic (generated)  ·  ⬜ Not cached"
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
    if st.button("🔄 Fetch from API", key="single_fetch", use_container_width=True):
        with st.spinner(f"Fetching {target_year}…"):
            success, msg = cache_year(target_year)
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
        generate_synthetic_year(target_year)
        st.success(f"🧪 Generated synthetic data for {target_year}.")
        st.cache_data.clear()
        time.sleep(1)
        st.rerun()

with single_cols[3]:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Delete Cache", key="single_del", use_container_width=True):
        delete_year_cache(target_year)
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

        Weather data is stored as **per-year CSV files** in `data/processed/weather/`.

        | File | Purpose |
        |------|---------|
        | `weather_2024.csv` | Daily mean temperatures for 2024 |
        | `weather_2023.csv` | Daily mean temperatures for 2023 |
        | `_cache_meta.json` | Tracks data source and timestamps |

        ### Data Sources (tried in order)

        | Priority | Source | Coverage |
        |----------|--------|----------|
        | 1️⃣ | **Environment Canada** (Toronto Pearson) | 1996–present, free, no API key |
        | 2️⃣ | **Open-Meteo Archive** (fallback) | When EnvCan unavailable |
        | 3️⃣ | **Synthetic** (auto-generated) | Always available, modeled pattern |

        ### Data Flow

        ```
        Peak Analytics page loads
            │
            ├─ Year cached? → Read from CSV ✅
            │
            └─ Year missing? → Auto-generate synthetic data 🟡
                               (so the dashboard never breaks)
        ```

        ### Status Legend

        - **✅ Environment Canada:** Real observed daily temps from Toronto Pearson
        - **✅ Open-Meteo:** Real data from Open-Meteo reanalysis
        - **🟡 Synthetic:** Modeled Toronto seasonal pattern (sine wave + noise)

        Use the **Fetch Range** button above to download real data.
        """
    )
