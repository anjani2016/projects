# src/finance/peak_engine.py
import numpy as np
import pandas as pd


class PeakMitigationEngine:

    def __init__(self, total_ga_pool: float = 3_000_000_000):
        """Initializes the engine with the estimated annual Ontario Class A GA pool pool.

        Default is roughly $3B CAD.
        """
        self.total_ga_pool = total_ga_pool

    def simulate_mitigation(
        self,
        df_client: pd.DataFrame,
        df_ieso_peaks: pd.DataFrame,
        curtailment_kw: float,
        battery_kw: float,
        battery_kwh: float,
        battery_eff: float = 0.85,
    ) -> dict:
        """Simulates historical peak contributions and mitigations.

        df_client columns: ['timestamp', 'client_kw'] df_ieso_peaks columns:
        ['timestamp', 'ieso_system_mw', 'peak_rank']
        """
        # Ensure timestamps are localized or matching
        df_client = df_client.set_index("timestamp")
        df_ieso_peaks = df_ieso_peaks.set_index("timestamp")

        # Join client demand directly onto the exact 5 peak hours of the year
        peak_events = df_ieso_peaks.join(df_client, how="inner")

        results = []
        for ts, row in peak_events.iterrows():
            orig_client_kw = row["client_kw"]
            ieso_mw = row["ieso_system_mw"]

            # 1. Simulate Curtailment
            post_curtail_kw = max(0.0, orig_client_kw - curtailment_kw)

            # 2. Simulate Battery Dispatch (Assume intelligent dispatch for the single peak hour)
            # Max energy battery can dump in 1 hour is bound by its capacity or max power output
            max_hourly_discharge = min(battery_kw, battery_kwh)
            post_battery_kw = max(0.0, post_curtail_kw - max_hourly_discharge)

            # Calculate peak factors
            orig_pf = (orig_client_kw / 1000) / ieso_mw  # Convert client kW to MW
            mitigated_pf = (post_battery_kw / 1000) / ieso_mw

            results.append(
                {
                    "timestamp": ts,
                    "peak_rank": row["peak_rank"],
                    "ieso_system_mw": ieso_mw,
                    "original_kw": orig_client_kw,
                    "mitigated_kw": post_battery_kw,
                    "curtailment_reduction_kw": orig_client_kw
                    - post_curtail_kw,
                    "battery_reduction_kw": post_curtail_kw - post_battery_kw,
                    "orig_pf": orig_pf,
                    "mitigated_pf": mitigated_pf,
                }
            )

        df_results = pd.DataFrame(results)

        if df_results.empty:
            return {
                "event_breakdown": df_results,
                "summary": {
                    "original_peak_factor": 0.0,
                    "mitigated_peak_factor": 0.0,
                    "original_ga_cost": 0.0,
                    "mitigated_ga_cost": 0.0,
                    "total_savings": 0.0,
                    "net_peak_reduction_kw": 0.0,
                },
            }

        # Totals and Financials
        orig_total_pf = df_results["orig_pf"].sum()
        mitigated_total_pf = df_results["mitigated_pf"].sum()

        orig_ga_cost = orig_total_pf * self.total_ga_pool
        mitigated_ga_cost = mitigated_total_pf * self.total_ga_pool
        total_savings = orig_ga_cost - mitigated_ga_cost

        return {
            "event_breakdown": df_results,
            "summary": {
                "original_peak_factor": orig_total_pf,
                "mitigated_peak_factor": mitigated_total_pf,
                "original_ga_cost": orig_ga_cost,
                "mitigated_ga_cost": mitigated_ga_cost,
                "total_savings": total_savings,
                "net_peak_reduction_kw": (
                    df_results["original_kw"] - df_results["mitigated_kw"]
                ).mean(),
            },
        }