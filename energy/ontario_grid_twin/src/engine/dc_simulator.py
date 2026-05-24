import geopandas as gpd
import pandas as pd
import numpy as np
import os

def run_simulation(target_substation_name, dc_load_mw):
    """
    Simulates the impact of a new Data Centre load on Ontario's grid.
    Uses Monte Carlo methods to determine reliability scores.
    """
    print(f"--- Phase 3: Digital Twin Simulation ({dc_load_mw}MW) ---")
    
    # 1. Load the analyzed data
    processed_path = 'data/processed/analyzed_substations.parquet'
    
    if not os.path.exists(processed_path):
        print("Error: Processed data not found. Run capacity_analyzer.py first.")
        return

    subs = gpd.read_parquet(processed_path)
    
    # Validate the substation exists
    if target_substation_name not in subs['name'].values:
        print(f"Error: {target_substation_name} not found.")
        return

    # Extract the specific node data
    sub_row = subs[subs['name'] == target_substation_name].iloc[0]

    # 2. Monte Carlo Simulation Logic
    iterations = 1000  # Increased for better statistical confidence
    successes = 0
    
    # Mapping the columns correctly now
    base_load = sub_row['current_load_mw']
    limit = sub_row['capacity_mw']

    print(f"Node: {target_substation_name} | Limit: {limit:.2f}MW | Base Load: {base_load:.2f}MW")
    print(f"Simulating {iterations} scenarios...")

    for _ in range(iterations):
        # Simulate 2026 Summer Peak variability (+/- 15%)
        peak_fluctuation = np.random.uniform(0.85, 1.15)
        simulated_ambient_load = base_load * peak_fluctuation
        
        # Total load = Existing grid load + New Data Centre
        total_load = simulated_ambient_load + dc_load_mw
        
        if total_load <= limit:
            successes += 1

    reliability_score = (successes / iterations) * 100

    # 3. I2R Loss Calculation (Engineering Metric)
    # Voltage check: 230kV vs 500kV impacts line efficiency
    voltage_kv = 230 if "230kV" in str(sub_row.get('voltage', '')) else 500
    resistance = 0.05  # Ohms (assumed for short-run transmission)
    
    # Current I = Power / Voltage
    current_amps = (dc_load_mw * 10**6) / (voltage_kv * 1000)
    losses_mw = (current_amps**2 * resistance) / 10**6

    print("\n--- Final Simulation Report ---")
    print(f"Reliability Probability: {reliability_score:.2f}%")
    print(f"Estimated Heat Loss (I^2R): {losses_mw:.4f} MW")
    
    if reliability_score >= 99:
        print("Conclusion: EXCELLENT. This node is a 'Green Zone' for development.")
    elif reliability_score >= 90:
        print("Conclusion: FEASIBLE. Requires IESO connection assessment.")
    else:
        print("Conclusion: HIGH RISK. This node likely requires a transformer upgrade.")

if __name__ == "__main__":
    # Test a 100MW Hyperscale Data Centre
    run_simulation(target_substation_name='Armitage TS', dc_load_mw=100)