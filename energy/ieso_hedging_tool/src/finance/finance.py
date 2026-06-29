# src/finance/finance.py
import numpy as np
from scipy.stats import norm

def calculate_energy_greeks(S, K, T, r, sigma, option_type="call"):
    """
    Calculates Black-Scholes Greeks and Premium for an energy option (Cap/Floor).
    S: Current Price (MWh)
    K: Strike Price
    T: Time to expiry (years)
    r: Risk-free rate (decimal)
    sigma: Volatility (decimal)
    """
    # Safety checks
    if T <= 0:
        intrinsic_value = max(0, S - K) if option_type == "call" else max(0, K - S)
        return {
            "Premium": round(intrinsic_value, 4),
            "Delta": 1.0 if (option_type == "call" and S > K) or (option_type == "put" and S < K) else 0.0,
            "Gamma": 0.0,
            "Vega": 0.0,
            "Theta": 0.0
        }
    
    if sigma <= 0:
        sigma = 1e-9

    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    if option_type == "call":
        premium = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        delta = norm.cdf(d1)
        theta = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * norm.cdf(d2)
    else:
        # Put option logic (Floor)
        premium = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = norm.cdf(d1) - 1
        theta = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-d2)

    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T)

    return {
        "Premium": round(premium, 4),
        "Delta": round(delta, 4),
        "Gamma": round(gamma, 4),
        "Vega": round(vega, 4),
        "Theta": round(theta, 4)
    }

def calculate_advanced_greeks(S, K, T, r, sigma):
    """
    Wraps the energy greeks calculation and ensures all keys are present.
    S: Spot, K: Strike, T: Time (years), r: Risk-free, sigma: Volatility
    """
    # For now, we use the same core logic but ensure the dictionary is complete
    return calculate_energy_greeks(S, K, T, r, sigma, option_type="call")

def calculate_ga_cost(mwh, ga_class="B", pdf=0.0, rate_b=60.0):
    """Calculates Global Adjustment based on Ontario consumer class."""
    if ga_class == "B":
        return mwh * rate_b
    
    # Class A logic: pdf is Peak Demand Factor
    monthly_ga_pool = 1.2e9  # Estimated monthly provincial GA pool
    return pdf * monthly_ga_pool
