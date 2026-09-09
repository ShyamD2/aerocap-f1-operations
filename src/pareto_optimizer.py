"""
src/pareto_optimizer.py
Multi-Objective Pareto Frontier Upgrade Strategy Engine
Optimizes: Downforce Gain (points) vs Cost-Cap Spend (£) vs Autoclave Capacity (Hours)
"""

import pandas as pd
import numpy as np


class ParetoUpgradeOptimizer:
    def __init__(self, max_budget_gbp=None, max_autoclave_hours=None, max_lead_time_days=None):
        self.max_budget_gbp = max_budget_gbp
        self.max_autoclave_hours = max_autoclave_hours
        self.max_lead_time_days = max_lead_time_days

    def identify_pareto_frontier(self, df_candidates):
        """
        Identifies non-dominated Pareto optimal solutions among upgrade candidates.
        
        Objectives:
        1. Maximize: projected_downforce_gain (points)
        2. Minimize: manufacturing_cost_gbp (£)
        3. Minimize: autoclave_hours (hours)
        4. Minimize: lap_time_delta_sec (seconds, more negative is faster)
        """
        df = df_candidates.copy()

        # Apply hard operational boundary constraints if specified
        if self.max_budget_gbp is not None:
            df = df[df["manufacturing_cost_gbp"] <= self.max_budget_gbp]
        if self.max_autoclave_hours is not None:
            df = df[df["autoclave_hours"] <= self.max_autoclave_hours]
        if self.max_lead_time_days is not None:
            df = df[df["lead_time_days"] <= self.max_lead_time_days]

        if df.empty:
            return df

        # Metrics for Pareto dominance
        # Vector A dominates Vector B if:
        # A.downforce >= B.downforce AND A.cost <= B.cost AND A.hours <= B.hours
        # AND at least one strict inequality holds.
        is_pareto = []
        n = len(df)
        df_reset = df.reset_index(drop=True)

        for i in range(n):
            dominated = False
            row_i = df_reset.iloc[i]
            for j in range(n):
                if i == j:
                    continue
                row_j = df_reset.iloc[j]
                
                # Check if j dominates i
                j_better_or_equal = (
                    row_j["projected_downforce_gain"] >= row_i["projected_downforce_gain"] and
                    row_j["manufacturing_cost_gbp"] <= row_i["manufacturing_cost_gbp"] and
                    row_j["autoclave_hours"] <= row_i["autoclave_hours"] and
                    row_j["lap_time_delta_sec"] <= row_i["lap_time_delta_sec"]
                )
                j_strictly_better = (
                    row_j["projected_downforce_gain"] > row_i["projected_downforce_gain"] or
                    row_j["manufacturing_cost_gbp"] < row_i["manufacturing_cost_gbp"] or
                    row_j["autoclave_hours"] < row_i["autoclave_hours"] or
                    row_j["lap_time_delta_sec"] < row_i["lap_time_delta_sec"]
                )
                if j_better_or_equal and j_strictly_better:
                    dominated = True
                    break
            is_pareto.append(not dominated)

        df_reset["is_pareto_optimal"] = is_pareto
        
        # Calculate Efficiency Metric: Cost per Millisecond Gained (£/ms)
        # 1 millisecond = 0.001 seconds
        df_reset["ms_gain"] = df_reset["lap_time_delta_sec"].apply(lambda x: abs(x) * 1000.0 if x < 0 else 0.0)
        df_reset["cost_per_ms_gbp"] = np.where(
            df_reset["ms_gain"] > 0,
            df_reset["manufacturing_cost_gbp"] / df_reset["ms_gain"],
            np.inf
        )
        df_reset["cost_per_ms_gbp"] = df_reset["cost_per_ms_gbp"].round(2)

        return df_reset

    def rank_optimal_packages(self, df_pareto):
        """Ranks Pareto optimal packages by cost-efficiency (£/ms gained)."""
        pareto_subset = df_pareto[df_pareto["is_pareto_optimal"]].copy()
        return pareto_subset.sort_values(by="cost_per_ms_gbp", ascending=True)
