import pandas as pd
import os

def analyze_york_capacity(threshold=0.85):
    """
    Identifies Regional Transformer Stations in York Region
    that are close to their thermal capacity limits.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    subs_path = os.path.join(base_dir, 'data/processed/analyzed_substations.parquet')
    
    if not os.path.exists(subs_path):
        print(f"Error: {subs_path} not found.")
        return None

    df = pd.read_parquet(subs_path)
    
    # Filter for Regional TS (using our logic or voltage)
    # In this dataset, they are all marked with TS or Junction
    # We can also use the grid_classifier if we import it
    from energy.ontario_grid_twin.src.engine.grid_classifier import add_grid_classification
    df = add_grid_classification(df)
    
    # Filter for Regional TS in York
    york_ts = df[df['grid_centre_type'] == 'Regional Transformer Station'].copy()
    
    if york_ts.empty:
        # Include Transmission too if they have TS in name (many 230kV stations are called TS)
        york_ts = df[df['name'].str.contains('TS|JUNCTION', case=False)].copy()

    # Calculate load percentage
    # If capacity_mw is missing, assume current_load + headroom
    if 'capacity_mw' not in york_ts.columns or york_ts['capacity_mw'].isnull().all():
        york_ts['capacity_mw'] = york_ts['current_load_mw'] + york_ts['headroom_mw']
    
    york_ts['load_factor'] = york_ts['current_load_mw'] / york_ts['capacity_mw']
    
    critical_stations = york_ts[york_ts['load_factor'] >= threshold].sort_values(by='load_factor', ascending=False)
    
    return critical_stations

if __name__ == "__main__":
    critical = analyze_york_capacity(threshold=0.90)
    if critical is not None:
        print(f"Critical Stations (>= 90% capacity):")
        print(critical[['name', 'voltage', 'current_load_mw', 'capacity_mw', 'load_factor']])
    else:
        print("No critical stations found.")
