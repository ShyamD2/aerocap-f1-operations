"""
tests/test_executive_briefing.py
Unit tests for Brackley Operations Executive Briefing Memo generator.
"""

from src.executive_briefing import ExecutiveBriefingGenerator


def test_briefing_generation_locked():
    memo = ExecutiveBriefingGenerator.generate_memo(
        session_name="Silverstone GP FP1",
        cci=0.62,
        gate3_locked=True,
        sunk_cost_saved_gbp=450000.0,
        certified_headroom_gbp=11000000.0,
        statutory_cap_gbp=109210000.0,
        blocked_rig_count=1,
        cell_oee_pct=91.5
    )
    assert "headline" in memo
    assert "directives" in memo
    assert "markdown_memo" in memo
    assert "STAGE GATE 3 AUTOCLAVE SPEND LOCKED" in memo["headline"]
    assert "£450,000.00" in memo["markdown_memo"]
    assert "Toto Wolff" in memo["markdown_memo"]


def test_briefing_generation_released():
    memo = ExecutiveBriefingGenerator.generate_memo(
        session_name="Silverstone GP FP2",
        cci=0.94,
        gate3_locked=False,
        sunk_cost_saved_gbp=0.0,
        certified_headroom_gbp=11000000.0,
        statutory_cap_gbp=109210000.0,
        blocked_rig_count=0,
        cell_oee_pct=95.0,
        active_upgrade_name="W16 Spec-B Venturi Floor"
    )
    assert "CORRELATION NOMINAL" in memo["headline"]
    assert "W16 Spec-B Venturi Floor" in memo["markdown_memo"]
