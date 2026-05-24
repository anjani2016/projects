import pandas as pd

def classify_substation(row):
    """
    Classifies a substation based on voltage and naming conventions
    as per the energy distribution schematic.
    """
    name = str(row.get('name', '')).upper()
    voltage = row.get('voltage', '')
    
    # Extract numeric voltage
    v_val = 0
    if pd.notnull(voltage):
        try:
            v_val = int(str(voltage).replace('kV', '').strip())
        except ValueError:
            pass

    # Logic:
    # 1. Transmission (Source): High Voltage (>= 230kV) or contains "SWITCHING" or "GENERATING"
    # 2. Regional TS: High Voltage input (115kV/230kV) to Medium Voltage output (44kV/27.6kV).
    #    In the schematic, TS are the step-down points.
    # 3. Demand Centres: Distribution substations stepping down to LV (<44kV).

    # Keyword-based classification (strongest indicator)
    if any(k in name for k in [" SS", "SWITCHING", "FLOW", "INTERFACE", "CONNECTION"]):
        return "Transmission Substation"
    elif any(k in name for k in [" TS", "TRANSFORMER", "REGIONAL"]):
        return "Regional Transformer Station"
    elif any(k in name for k in [" DS", "DISTRIBUTION", "DEMAND"]):
        return "Demand Centre (Distribution)"
    
    # Voltage-based fallback (if no keywords present)
    if v_val >= 500:
        return "Transmission Substation"
    elif v_val >= 115:
        return "Regional Transformer Station"
    else:
        return "Demand Centre (Distribution)"

def add_grid_classification(df):
    """
    Adds a 'grid_centre_type' column to the dataframe.
    """
    if df is not None and not df.empty:
        df['grid_centre_type'] = df.apply(classify_substation, axis=1)
    return df

if __name__ == "__main__":
    # Quick test
    test_data = [
        {'name': 'Claireville TS', 'voltage': '230kV'},
        {'name': 'Cherrywood SS', 'voltage': '500kV'},
        {'name': 'Richmond Hill DS', 'voltage': '27.6kV'},
        {'name': 'York Region Regional Station', 'voltage': '115kV'}
    ]
    df = pd.DataFrame(test_data)
    df = add_grid_classification(df)
    print(df[['name', 'grid_centre_type']])
