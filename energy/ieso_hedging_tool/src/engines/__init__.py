# src/engines/__init__.py
# Re-exports the public API of the engines package.
# Consumers can import directly from src.engines without knowing which submodule holds the function.
from energy.ieso_hedging_tool.src.engines.ingestion_peakhours import fetch_live_ieso_demand
from energy.ieso_hedging_tool.src.engines.weather_engine import (
    fetch_multi_year_weather,
    fetch_daily_weather,
    cache_year,
    generate_synthetic_year,
    delete_year_cache,
    load_cache_meta,
)
from energy.ieso_hedging_tool.src.engines.scraper import fetch_ieso_data, save_raw_data
from energy.ieso_hedging_tool.src.engines.ieso_engine import (
    fetch_historical_grid_matrix,
    cache_year_ieso,
    generate_synthetic_year_ieso,
    delete_year_cache_ieso,
    load_cache_meta_ieso,
)

