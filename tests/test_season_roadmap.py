"""
tests/test_season_roadmap.py
Unit tests for 24-race season roadmap engine and crash headroom calculations.
"""

from src.season_roadmap import SeasonRoadmapEngine


def test_season_roadmap_clean_baseline():
    engine = SeasonRoadmapEngine(calendar_races=24, sprint_count=6)
    res = engine.simulate_season(active_upgrade_ids=[], crash_scenario_key="Clean Season (No Major Damage)")
    
    assert "trajectory_df" in res
    assert len(res["trajectory_df"]) == 24
    assert res["final_headroom_gbp"] > 0
    assert not res["is_breach"]
    assert res["crash_cost_gbp"] == 0.0


def test_season_roadmap_upgrades_accumulate():
    engine = SeasonRoadmapEngine(calendar_races=24, sprint_count=6)
    active_upgs = ["UPG_ESP_SPEC_B_FLOOR", "UPG_GBR_SIDEPOD_UNDERCUT"]
    res = engine.simulate_season(active_upgrade_ids=active_upgs, crash_scenario_key="Clean Season (No Major Damage)")
    
    expected_spend = 450000.0 + 320000.0
    assert res["total_upgrade_spend_gbp"] == expected_spend
    assert res["total_laptime_gain_ms"] == 240.0 # 150 + 90
    assert res["cost_per_ms_overall"] > 0


def test_season_roadmap_catastrophic_crash_impact():
    engine = SeasonRoadmapEngine(calendar_races=24, sprint_count=6)
    res_clean = engine.simulate_season(active_upgrade_ids=[], crash_scenario_key="Clean Season (No Major Damage)")
    res_crash = engine.simulate_season(active_upgrade_ids=[], crash_scenario_key="Catastrophic Turn 1 Multi-Car Chassis Scrappage")
    
    assert res_crash["crash_cost_gbp"] == 1450000.0
    assert res_crash["final_headroom_gbp"] < res_clean["final_headroom_gbp"]
    assert abs((res_clean["final_headroom_gbp"] - res_crash["final_headroom_gbp"]) - 1450000.0) < 1.0
