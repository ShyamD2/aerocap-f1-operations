"""
tests/test_pdf.py
Unit tests for Official FIA Statutory Compliance PDF Dossier Generator
"""

import pandas as pd
from src.pdf_generator import FIAPDFReportGenerator


def test_pdf_generation_success():
    generator = FIAPDFReportGenerator(team_name="Mercedes-Benz Grand Prix Limited", registration_ref="835")
    
    mock_summary = {
        "gross_expenses_usd": 155_000_000.0,
        "excluded_expenses_usd": 38_000_000.0,
        "used_inventory_added_usd": 14_000_000.0,
        "redundant_inventory_written_off_usd": 1_800_000.0,
        "unused_inventory_deducted_usd": 5_200_000.0,
        "net_relevant_costs_usd": 127_600_000.0,
        "net_relevant_costs_gbp": 127_600_000.0 / 1.2691,
        "statutory_cap_usd": 138_600_000.0,
        "statutory_cap_gbp": 138_600_000.0 / 1.2691,
        "cost_cap_headroom_usd": 11_000_000.0,
        "cost_cap_headroom_gbp": 11_000_000.0 / 1.2691,
        "capex_limit_usd": 42_000_000.0,
        "capex_spent_usd": 18_200_000.0,
        "capex_headroom_usd": 23_800_000.0,
        "breach_category": "COMPLIANT"
    }

    df_excl = pd.DataFrame([
        {"exclusion_clause": "Art. 3.1(a) Marketing Activities", "amount_usd": 4_200_000.0},
        {"exclusion_clause": "Art. 3.1(b) F1 Driver Retainer", "amount_usd": 22_000_000.0}
    ])

    pdf_bytes = generator.generate_pdf_bytes(mock_summary, df_excl)
    assert len(pdf_bytes) > 1000
    # Standard PDF magic byte signature
    assert pdf_bytes.startswith(b"%PDF")
