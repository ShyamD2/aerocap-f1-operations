"""
tests/test_pareto.py
Unit tests for Multi-Objective Pareto Frontier Upgrade Strategy Engine
"""

import pandas as pd
from src.pareto_optimizer import ParetoUpgradeOptimizer


def test_pareto_dominance():
    optimizer = ParetoUpgradeOptimizer()
    
    # Candidate A: High Downforce (20), High Cost (£300k), High Hours (40), Lap Delta (-0.20s)
    # Candidate B: Moderate Downforce (15), Moderate Cost (£200k), Moderate Hours (25), Lap Delta (-0.15s)
    # Candidate C: Inferior/Dominated by B: Lower Downforce (10), Higher Cost (£250k), Higher Hours (30), Lap Delta (-0.10s)
    df_candidates = pd.DataFrame([
        {"upgrade_code": "PKG-A", "projected_downforce_gain": 20.0, "manufacturing_cost_gbp": 300_000.0, "autoclave_hours": 40.0, "lap_time_delta_sec": -0.20, "lead_time_days": 14},
        {"upgrade_code": "PKG-B", "projected_downforce_gain": 15.0, "manufacturing_cost_gbp": 200_000.0, "autoclave_hours": 25.0, "lap_time_delta_sec": -0.15, "lead_time_days": 10},
        {"upgrade_code": "PKG-C", "projected_downforce_gain": 10.0, "manufacturing_cost_gbp": 250_000.0, "autoclave_hours": 30.0, "lap_time_delta_sec": -0.10, "lead_time_days": 12},
    ])

    res = optimizer.identify_pareto_frontier(df_candidates)
    
    a_pareto = res.loc[res["upgrade_code"] == "PKG-A", "is_pareto_optimal"].iloc[0]
    b_pareto = res.loc[res["upgrade_code"] == "PKG-B", "is_pareto_optimal"].iloc[0]
    c_pareto = res.loc[res["upgrade_code"] == "PKG-C", "is_pareto_optimal"].iloc[0]

    assert a_pareto == True
    assert b_pareto == True
    assert c_pareto == False  # C is strictly dominated by B


def test_cost_per_millisecond_metric():
    optimizer = ParetoUpgradeOptimizer()
    df_candidates = pd.DataFrame([
        {"upgrade_code": "PKG-B", "projected_downforce_gain": 15.0, "manufacturing_cost_gbp": 200_000.0, "autoclave_hours": 25.0, "lap_time_delta_sec": -0.10, "lead_time_days": 10},
    ])
    res = optimizer.identify_pareto_frontier(df_candidates)
    # -0.10s = 100ms. £200,000 / 100ms = £2,000 / ms
    assert res.iloc[0]["cost_per_ms_gbp"] == 2000.0
