"""
tests/test_audit_pack.py
Unit tests for FIA Statutory Audit Pack Exporter
"""

import pandas as pd
from src.audit_pack_generator import FIAAuditPackGenerator


def test_audit_pack_generation():
    generator = FIAAuditPackGenerator(team_name="Mercedes-Benz Grand Prix Limited", registration_ref="835")
    
    mock_summary = {
        "gross_expenses_usd": 150_000_000.0,
        "excluded_expenses_usd": 35_000_000.0,
        "used_inventory_added_usd": 12_000_000.0,
        "redundant_inventory_written_off_usd": 1_500_000.0,
        "unused_inventory_deducted_usd": 4_000_000.0,
        "net_relevant_costs_usd": 124_500_000.0,
        "net_relevant_costs_gbp": 124_500_000.0 / 1.2691,
        "statutory_cap_usd": 138_600_000.0,
        "statutory_cap_gbp": 138_600_000.0 / 1.2691,
        "cost_cap_headroom_usd": 14_100_000.0,
        "cost_cap_headroom_gbp": 14_100_000.0 / 1.2691,
        "capex_limit_usd": 42_000_000.0,
        "capex_spent_usd": 14_500_000.0,
        "capex_headroom_usd": 27_500_000.0,
        "breach_category": "COMPLIANT"
    }

    df_excl = pd.DataFrame([
        {"exclusion_clause": "Art. 3.1(a) Marketing Activities", "amount_usd": 4_200_000.0},
        {"exclusion_clause": "Art. 3.1(b) F1 Driver Consideration", "amount_usd": 22_000_000.0},
    ])

    report = generator.generate_markdown_audit_report(mock_summary, df_excl, pd.DataFrame())

    assert "FIA FORMULA 1 FINANCIAL REGULATIONS COMPLIANCE DOSSIER" in report
    assert "Mercedes-Benz Grand Prix Limited" in report
    assert "Article 2 & Article 4" in report
    assert "Article 3.1 Excluded Costs Schedule" in report
    assert "COMPLIANT" in report
    assert "Team Principal & CEO" in report
