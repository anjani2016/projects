#!/usr/bin/env python3
"""
main.py - CLI Entrypoint for the IESO Hedging Tool.
Used for headless execution, data backfills, risk simulations, and cron tasks.
"""
import argparse
import logging
import sys
import os
import pandas as pd

# Adjust path if needed to ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 1. Establish project-wide logging configuration before any other imports
from energy.ieso_hedging_tool.src.core.utils import setup_logger, initialize_project
setup_logger(log_level=logging.INFO)

# Module-level logger — labelled as '__main__' in the log output
logger = logging.getLogger(__name__)
logger.info("IESO Hedging Tool CLI starting up...")

from energy.ieso_hedging_tool.src.engines.scraper import fetch_ieso_data, save_raw_data
from energy.ieso_hedging_tool.src.finance.models import EnergySimulator
from energy.ieso_hedging_tool.src.finance.finance import calculate_energy_greeks

def run_fetch(year_month):
    """Headless scraper action."""
    logger.info("Starting IESO Day-Ahead LMP fetching for: %s", year_month)
    initialize_project()
    data = fetch_ieso_data(year_month)

    if isinstance(data, pd.DataFrame):
        path = save_raw_data(data, year_month)
        logger.info("Success: Downloaded %d rows. Saved to %s", len(data), path)
        logger.info("Average Ontario Price: $%.2f/MWh", data['Ontario Price'].mean())
        logger.info("Peak Zonal Price:      $%.2f/MWh", data['Ontario Price'].max())
    else:
        logger.error("Scrape failed: %s", data)
        sys.exit(1)

def run_simulation(s0, mu, theta, sigma, steps):
    """Headless Monte Carlo simulation run."""
    logger.info(
        "Running Ornstein-Uhlenbeck simulation — s0=%.2f, mu=%.2f, theta=%.4f, sigma=%.4f, steps=%d",
        s0, mu, theta, sigma, steps,
    )

    sim = EnergySimulator(s0=s0, mu=mu, theta=theta, sigma=sigma)
    path = sim.run_monte_carlo(n_steps=steps)

    logger.info("Simulation completed.")
    logger.info("  Terminal Price:  $%.2f/MWh", path[-1])
    logger.info("  Max Price Path:  $%.2f/MWh", path.max())
    logger.info("  Min Price Path:  $%.2f/MWh", path.min())
    logger.info("  Mean Price Path: $%.2f/MWh", path.mean())

def main():
    parser = argparse.ArgumentParser(
        description="IESO Energy Hedging Tool - Headless CLI and Engine Room Manager",
        epilog="Designed by Centauri Research (Antigravity Framework)"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument(
        "--fetch-data", 
        metavar="YYYYMM",
        help="Fetch and cache Day-Ahead Hourly LMP reports for specified year and month (e.g. 202603)"
    )
    
    group.add_argument(
        "--simulate", 
        action="store_true",
        help="Run a headless Ornstein-Uhlenbeck stochastic simulation path"
    )
    
    group.add_argument(
        "--info",
        action="store_true",
        help="Print project structural information and configurations"
    )
    
    # Simulation sub-parameters
    parser.add_argument("--s0", type=float, default=40.0, help="Initial Spot Price (default: 40.0)")
    parser.add_argument("--mu", type=float, default=35.0, help="Long-term equilibrium mean price (default: 35.0)")
    parser.add_argument("--theta", type=float, default=0.15, help="Rate of mean reversion speed (default: 0.15)")
    parser.add_argument("--sigma", type=float, default=2.5, help="Volatility parameter (default: 2.5)")
    parser.add_argument("--steps", type=int, default=720, help="Number of steps/hours to simulate (default: 720)")

    args = parser.parse_args()

    if args.fetch_data:
        run_fetch(args.fetch_data)
    elif args.simulate:
        run_simulation(args.s0, args.mu, args.theta, args.sigma, args.steps)
    elif args.info:
        print("Centauri Research - IESO Energy Hedging Digital Twin")
        print("==================================================")
        print("Root directory layout follows the unified architecture:")
        print("  - src/core:      Infrastructure & Database Pool Helpers")
        print("  - src/engines:   IESO Public API & Scraping Ingestion engines")
        print("  - src/finance:   Black-Scholes quantitative models & OU processes")
        print("  - database/:     TimescaleDB migration schema and query isolation")
        print("  - pages/:        Multi-page presentation layout for UI")

if __name__ == "__main__":
    main()