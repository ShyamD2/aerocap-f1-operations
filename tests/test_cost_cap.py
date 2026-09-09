"""
tests/test_cost_cap.py
Unit tests verifying strict compliance with FIA Financial Regulations (Issue 24)
"""

import pytest
import pandas as pd
from src.cost_cap_engine import FIACostCapEngine
from src.config import (
    BASE_COST_CAP_USD,
    PER_COMPETITION_DELTA_USD,
    SPRINT_DEDUCTION_USD,
    INITIAL_APPLICABLE_RATE_GBP,
    MERCEDES_CAPEX_LIMIT_USD
)


def test_statutory_cap_calculation():
    # 24 races, 6 sprints
    engine = FIACostCapEngine(calendar_races=24, sprint_count=6)
    expected_cap = BASE_COST_CAP_USD + (3 * PER_COMPETITION_DELTA_USD) - (6 * SPRINT_DEDUCTION_USD)
    # $135M + $5.4M - $1.8M = $138.6M
    assert engine.base_cap_usd == 138_600_000.0
    assert round(engine.statutory_cap_gbp, 2) == round(138_600_000.0 / INITIAL_APPLICABLE_RATE_GBP, 2)


def test_article_3_exclusions_classification():
    engine = FIACostCapEngine()
    test_cases = [
        ({"cost_centre": "Marketing", "account_desc": "VIP Lounge"}, True, "Art. 3.1(a)"),
        ({"cost_centre": "Executive", "account_desc": "Driver_Salary_Primary"}, True, "Art. 3.1(b)"),
        ({"cost_centre": "Executive", "account_desc": "Excluded_Person_Bonus"}, True, "Art. 3.1(d)"),
        ({"cost_centre": "Travel_Office", "account_desc": "Trackside Flight booking"}, True, "Art. 3.1(r)"),
        ({"cost_centre": "Sustainability", "account_desc": "Solar Farm Inverters"}, True, "Art. 3.1(y)"),
        ({"cost_centre": "Finance", "account_desc": "Bank Loan Interest"}, True, "Art. 3.1(f)"),
        ({"cost_centre": "Finance", "account_desc": "Corporate Income_Tax"}, True, "Art. 3.1(g)"),
        ({"cost_centre": "Applied_Science", "account_desc": "Hydrofoil CFD Run"}, True, "Art. 3.1(h)"),
        ({"cost_centre": "Composites_Mfg", "account_desc": "Carbon Pre-preg rolls"}, False, "Relevant Cost"),
    ]

    for row, expected_excl, keyword in test_cases:
        is_excl, clause = engine.classify_article_3_exclusions(row)
        assert is_excl == expected_excl
        assert keyword in clause


def test_td017_inventory_accounting():
    engine = FIACostCapEngine(calendar_races=24, sprint_count=6)
    
    # Mock expenses
    df_exp = pd.DataFrame([
        {"amount_usd": 100_000_000.0, "amount_gbp": 100_000_000.0/1.2691, "cost_centre": "Mfg", 
         "account_desc": "Chassis raw materials", "is_capex": 0}
    ])
    
    # Mock inventory under TD017
    df_inv = pd.DataFrame([
        {"part_number": "P1", "unit_cost_usd": 500_000.0, "inventory_status": "Used"},
        {"part_number": "P2", "unit_cost_usd": 800_000.0, "inventory_status": "Unused"},
        {"part_number": "P3", "unit_cost_usd": 250_000.0, "inventory_status": "Redundant"}
    ])

    summary, _ = engine.process_compliance_audit(df_exp, df_inv)
    
    # Relevant costs must include Used ($500k) and Redundant ($250k), but NOT Unused ($800k)
    expected_relevant = 100_000_000.0 + 500_000.0 + 250_000.0
    assert summary["net_relevant_costs_usd"] == expected_relevant
    assert summary["breach_category"] == "COMPLIANT"


def test_breach_thresholds():
    engine = FIACostCapEngine(calendar_races=21, sprint_count=0) # Cap = $135M
    
    # Case A: Minor Overspend (e.g. $138M -> +2.22% < 5%)
    df_minor = pd.DataFrame([
        {"amount_usd": 138_000_000.0, "amount_gbp": 138_000_000.0/1.2691, "cost_centre": "Mfg", 
         "account_desc": "Operations", "is_capex": 0}
    ])
    summary_minor, _ = engine.process_compliance_audit(df_minor, pd.DataFrame())
    assert "MINOR OVERSPEND BREACH" in summary_minor["breach_category"]

    # Case B: Material Overspend (e.g. $145M -> +7.4% >= 5%)
    df_mat = pd.DataFrame([
        {"amount_usd": 145_000_000.0, "amount_gbp": 145_000_000.0/1.2691, "cost_centre": "Mfg", 
         "account_desc": "Operations", "is_capex": 0}
    ])
    summary_mat, _ = engine.process_compliance_audit(df_mat, pd.DataFrame())
    assert "MATERIAL OVERSPEND BREACH" in summary_mat["breach_category"]
