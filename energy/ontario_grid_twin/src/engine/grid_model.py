from typing import Dict, List
import numpy as np

class GridNode:
    """
    A professional-grade class to represent a grid substation.
    Encapsulates both data and simulation logic.
    """
    def __init__(self, name: str, capacity_mw: float, base_load_mw: float, voltage_kv: int):
        self.name = name
        self.capacity_mw = capacity_mw
        self.base_load_mw = base_load_mw
        self.voltage_kv = voltage_kv

    def simulate_loads(self, new_load_mw: float, iterations: int = 1000) -> np.ndarray:
        """
        Runs Monte Carlo simulation using a Triangular Distribution and returns raw load array.
        """
        peak_demand = self.base_load_mw
        typical_demand = peak_demand * 0.70
        min_demand = peak_demand * 0.40
        
        ambient_loads = np.random.triangular(min_demand, typical_demand, peak_demand, iterations)
        return ambient_loads + new_load_mw

    def calculate_reliability(self, new_load_mw: float, iterations: int = 1000) -> float:
        """
        Performs a Monte Carlo simulation to determine the probability 
        that the node stays within capacity limits.
        """
        simulated_loads = self.simulate_loads(new_load_mw, iterations)
        successes = np.sum(simulated_loads <= self.capacity_mw)
        return (successes / iterations) * 100

    def estimate_losses(self, load_mw: float, resistance_ohms: float = 0.05) -> float:
        """
        Calculates I^2R losses based on simulated load and voltage.
        """
        # Current (Amps) = Power (Watts) / (Voltage (Volts))
        current = (load_mw * 1e6) / (self.voltage_kv * 1e3)
        losses_mw = (current**2 * resistance_ohms) / 1e6
        return losses_mw

# Example Usage:
if __name__ == "__main__":
    # Initializing Armitage TS with data from our previous steps
    armitage = GridNode(name="Armitage TS", capacity_mw=1250, base_load_mw=1050, voltage_kv=230)
    
    reliability = armitage.calculate_reliability(new_load_mw=100)
    print(f"Reliability for 100MW load: {reliability:.2f}%")