# engines/weather_engine.py
"""
Historical weather data engine for the GTA region.

Primary source: Environment Canada Climate Data (free, no API key, 30+ years)
  - Station 5097  (Toronto Pearson legacy)  → 1996–2013
  - Station 51459 (Toronto Intl A, current) → 2013–present

Fallback: Open-Meteo Archive API (when available)
Local cache: Per-year CSV files in data/processed/weather/
"""
import csv
import datetime
import io
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import streamlit as st

# ─── Path configuration ──────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CACHE_DIR = _PROJECT_ROOT / "data" / "processed" / "weather"
_META_FILE = _CACHE_DIR / "_cache_meta.json"

# Environment Canada station IDs for Toronto Pearson
_EC_STATIONS = [
    {"id": 51459, "name": "TORONTO INTL A",              "start": 2013, "end": 9999},
    {"id": 5097,  "name": "TORONTO LESTER B. PEARSON",   "start": 1996, "end": 2013},
]


def _ensure_cache_dir():
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _year_cache_path(year: int) -> Path:
    return _CACHE_DIR / f"weather_{year}.csv"


# ─── Metadata helpers ────────────────────────────────────────────────────────

def load_cache_meta() -> dict:
    """Load the cache metadata JSON. Returns dict keyed by year (str)."""
    if _META_FILE.exists():
        try:
            return json.loads(_META_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_cache_meta(meta: dict):
    _ensure_cache_dir()
    _META_FILE.write_text(json.dumps(meta, indent=2))


def _update_meta(year: int, source: str):
    """Mark a year's cache status. source = 'environment_canada' | 'open_meteo' | 'synthetic'."""
    meta = load_cache_meta()
    meta[str(year)] = {
        "source": source,
        "cached_at": datetime.datetime.now().isoformat(),
    }
    _save_cache_meta(meta)


# ─── Environment Canada fetch ────────────────────────────────────────────────

def _pick_ec_station(year: int) -> dict | None:
    """Select the best Environment Canada station for the given year."""
    for stn in _EC_STATIONS:
        if stn["start"] <= year <= stn["end"]:
            return stn
    return None


def _fetch_year_environment_canada(year: int) -> pd.DataFrame | None:
    """
    Fetch daily mean temperature for one year from Environment Canada.
    Returns DataFrame with [Timestamp, Temperature] or None on failure.
    """
    station = _pick_ec_station(year)
    if station is None:
        return None

    url = (
        f"https://climate.weather.gc.ca/climate_data/bulk_data_e.html?"
        f"format=csv&stationID={station['id']}&Year={year}&Month=1&Day=14&timeframe=2"
    )
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        reader = csv.reader(io.StringIO(response.text))
        rows = list(reader)
        if len(rows) < 2:
            return None

        header = rows[0]
        # Find column indices
        date_idx = next(i for i, c in enumerate(header) if "Date/Time" in c)
        temp_idx = next(
            i for i, c in enumerate(header)
            if "Mean Temp" in c and "Flag" not in c
        )

        records = []
        for row in rows[1:]:
            if len(row) > max(date_idx, temp_idx) and row[temp_idx].strip():
                try:
                    records.append({
                        "Timestamp": pd.Timestamp(row[date_idx].strip()),
                        "Temperature": float(row[temp_idx].strip()),
                    })
                except (ValueError, TypeError):
                    continue

        if not records:
            return None

        return pd.DataFrame(records)

    except Exception:
        return None


# ─── Open-Meteo fallback ─────────────────────────────────────────────────────

def _fetch_year_open_meteo(year: int) -> pd.DataFrame | None:
    """Fallback: fetch from Open-Meteo archive API."""
    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude=43.65&longitude=-79.61"
        f"&start_date={year}-01-01&end_date={year}-12-31"
        f"&daily=temperature_2m_mean&timezone=America%2FNew_York"
    )
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json().get("daily", {})
        df = pd.DataFrame({
            "Timestamp": pd.to_datetime(data.get("time")),
            "Temperature": data.get("temperature_2m_mean"),
        })
        return df if not df.empty else None
    except Exception:
        return None


# ─── Public cache management functions ────────────────────────────────────────

def cache_year(year: int) -> tuple[bool, str]:
    """
    Attempt to fetch & cache a single year.
    Tries Environment Canada first, then Open-Meteo as fallback.
    Returns (success, message).
    """
    _ensure_cache_dir()

    # Try Environment Canada first
    df = _fetch_year_environment_canada(year)
    if df is not None and not df.empty:
        df.to_csv(_year_cache_path(year), index=False)
        _update_meta(year, "environment_canada")
        return True, f"✅ {year}: Cached {len(df)} days from Environment Canada."

    # Fallback to Open-Meteo
    df = _fetch_year_open_meteo(year)
    if df is not None and not df.empty:
        df.to_csv(_year_cache_path(year), index=False)
        _update_meta(year, "open_meteo")
        return True, f"✅ {year}: Cached {len(df)} days from Open-Meteo (fallback)."

    return False, f"❌ {year}: Both Environment Canada and Open-Meteo failed."


def generate_synthetic_year(year: int):
    """Generate and cache synthetic weather data for a single year."""
    _ensure_cache_dir()
    np.random.seed(year)
    dates = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    day_of_year = dates.dayofyear
    warming_offset = max(0, (year - 1996) * 0.03)
    base_temp = 8 + warming_offset + 18 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
    noise = np.random.normal(0, 3.0, len(dates))
    df = pd.DataFrame({
        "Timestamp": dates,
        "Temperature": np.round(base_temp + noise, 1),
    })
    df.to_csv(_year_cache_path(year), index=False)
    _update_meta(year, "synthetic")


def delete_year_cache(year: int):
    """Remove cached data for a single year."""
    path = _year_cache_path(year)
    if path.exists():
        path.unlink()
    meta = load_cache_meta()
    meta.pop(str(year), None)
    _save_cache_meta(meta)


# ─── Main aggregation function (used by Peak Analytics) ──────────────────────

def fetch_multi_year_weather(start_year: int = 2023, end_year: int = 2025) -> pd.DataFrame:
    """
    Loads weekly-averaged weather data for the requested year range.
    Reads from per-year CSV cache files. If a year is missing, generates
    synthetic data as a fallback so the dashboard never breaks.
    """
    _ensure_cache_dir()
    frames = []

    for year in range(start_year, end_year + 1):
        path = _year_cache_path(year)
        if path.exists():
            try:
                frames.append(pd.read_csv(path, parse_dates=["Timestamp"]))
                continue
            except Exception:
                pass
        # No cache — generate synthetic so the page still works
        generate_synthetic_year(year)
        try:
            frames.append(pd.read_csv(path, parse_dates=["Timestamp"]))
        except Exception:
            pass

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df["Year"] = df["Timestamp"].dt.year.astype(str)
    df["Week"] = df["Timestamp"].dt.isocalendar().week

    weekly_df = df.groupby(["Year", "Week"])["Temperature"].mean().reset_index()
    return weekly_df

def fetch_daily_weather(start_year: int = 2023, end_year: int = 2025) -> pd.DataFrame:
    """Loads raw daily weather data without weekly aggregation."""
    _ensure_cache_dir()
    frames = []

    for year in range(start_year, end_year + 1):
        path = _year_cache_path(year)
        if path.exists():
            try:
                frames.append(pd.read_csv(path, parse_dates=["Timestamp"]))
                continue
            except Exception:
                pass
        generate_synthetic_year(year)
        try:
            frames.append(pd.read_csv(path, parse_dates=["Timestamp"]))
        except Exception:
            pass

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df["Date"] = df["Timestamp"].dt.date
    return df