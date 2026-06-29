# src/finance/models.py
# Contains the Ornstein-Uhlenbeck class. By isolating this, we can unit-test the simulation without needing a web browser or internet connection.
import numpy as np

class PriceSimulator_static:
    """Handles mean-reversion logic."""
    @staticmethod
    def simulate_ou(s0, mu, theta, sigma, dt=1, n_steps=720):
        prices_static = np.zeros(n_steps)
        prices_static[0] = s0
        for t in range(1, n_steps):
            drift = theta * (mu - prices_static[t-1]) * dt
            noise = sigma * np.sqrt(dt) * np.random.normal()
            prices_static[t] = prices_static[t-1] + drift + noise
        return prices_static
    

class EnergySimulator:
    """Mean-reverting price simulation (OU Process)."""
    def __init__(self, s0, mu, theta, sigma):
        self.s0 = s0        # Initial price
        self.mu = mu        # Long-term mean
        self.theta = theta  # Reversion speed
        self.sigma = sigma  # Volatility

    def run_monte_carlo(self, n_steps=720, dt=1):
        prices = np.zeros(n_steps)
        prices[0] = self.s0
        for t in range(1, n_steps):
            # OU Equation: dXt = theta(mu - Xt)dt + sigma * dWt
            drift = self.theta * (self.mu - prices[t-1]) * dt
            noise = self.sigma * np.sqrt(dt) * np.random.normal()
            prices[t] = prices[t-1] + drift + noise
        return prices
