import geopandas as gpd
import pandas as pd

def calculate_headroom():
    print("--- Running Headroom Analysis ---")
    
    # Load Data
    subs = gpd.read_parquet('data/raw/york_substations.parquet')
    forecast = pd.read_csv('data/raw/ieso_2026_forecast.csv')
    
    # Filter for York forecast
    york_data = forecast[forecast['region'] == 'York'].iloc[0]
    
    # Assumptions
    SAFETY_FACTOR = 1.15  # 15% reserve for reliability
    # Assume York's total capacity is split among its main substations for this simulation
    capacity_per_sub = york_data['available_capacity_mw'] / len(subs)
    demand_per_sub = york_data['peak_demand_mw_2026'] / len(subs)
    
    # Calculate Headroom
    subs['capacity_mw'] = capacity_per_sub
    subs['current_load_mw'] = demand_per_sub
    subs['headroom_mw'] = subs['capacity_mw'] - (subs['current_load_mw'] * SAFETY_FACTOR)
    
    # Round for cleanliness
    subs['headroom_mw'] = subs['headroom_mw'].clip(lower=0).round(2)
    
    print("\nCalculated Headroom for York Substations:")
    print(subs[['name', 'voltage', 'headroom_mw']])
    
    # Save processed data
    subs.to_parquet('data/processed/analyzed_substations.parquet')
    print("\nSuccess: Saved analyzed data to data/processed/")

if __name__ == "__main__":
    calculate_headroom()