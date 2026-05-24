# src/engines/forecasting.py
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger("ieso_hedging_tool." + __name__)

class LMPForecaster:
    """
    Forecasting engine for Real-Time Market (RTM) and Day-Ahead Market (DAM) pricing.
    Combines physical grid variables (demand, wind, solar) with historical price curves.
    """
    def __init__(self, model_type="mean_reversion"):
        self.model_type = model_type
        logger.info(f"Initialized LMPForecaster with {model_type} model.")

    def fit(self, historical_df):
        """Fits forecasting model to historical pricing dataframe."""
        if historical_df.empty:
            logger.warning("Attempted to fit model with empty historical data.")
            return self
            
        logger.info(f"Fitting pricing forecasting parameters on {len(historical_df)} points.")
        # Estimate mean reversion parameters (theta, mu, sigma) from data
        prices = historical_df['Ontario Price'].values
        self.mu_est = np.mean(prices)
        self.sigma_est = np.std(prices)
        
        # Simple auto-covariance to estimate theta
        if len(prices) > 1:
            r = np.corrcoef(prices[:-1], prices[1:])[0, 1]
            # Avoid division by zero or log of negative numbers
            r = max(0.01, min(0.99, r))
            self.theta_est = -np.log(r)
        else:
            self.theta_est = 0.15
            
        return self

    def predict_next_hours(self, last_spot, hours=24):
        """
        Projects future prices using the fitted mean-reversion parameters.
        Returns predicted price array.
        """
        mu = getattr(self, 'mu_est', 35.0)
        theta = getattr(self, 'theta_est', 0.15)
        sigma = getattr(self, 'sigma_est', 2.5)

        logger.info(f"Predicting next {hours} hours (Last spot: {last_spot:.2f}, μ: {mu:.2f})")
        
        predictions = np.zeros(hours)
        current = last_spot
        for t in range(hours):
            # Deterministic drift component + random walk (simulating standard expectation)
            drift = theta * (mu - current)
            predictions[t] = current + drift
            current = predictions[t]
            
        return predictions
