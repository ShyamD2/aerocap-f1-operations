"""
tests/test_stage_gate.py
Unit tests for Correlation-Gated Stage Release
"""

from src.stage_gate import StageGateManager


def test_gate_release_authorized():
    manager = StageGateManager(min_cci_for_production=0.85)
    res = manager.evaluate_gate_release(
        component_code="W16-FL-001",
        cci_score=0.91,
        planned_tooling_cost_gbp=320_000.0,
        planned_autoclave_hours=48.0
    )
    assert res["decision"] == "RELEASE_AUTHORIZED"
    assert res["funds_committed_gbp"] == 320_000.0
    assert res["funds_protected_gbp"] == 0.0


def test_gate_release_locked():
    manager = StageGateManager(min_cci_for_production=0.85)
    res = manager.evaluate_gate_release(
        component_code="W16-FL-002",
        cci_score=0.64,
        planned_tooling_cost_gbp=450_000.0,
        planned_autoclave_hours=56.0
    )
    assert res["decision"] == "PRODUCTION_LOCKED"
    assert res["funds_committed_gbp"] == 0.0
    # Confirms £450,000 in potential scrap was saved
    assert res["funds_protected_gbp"] == 450_000.0
