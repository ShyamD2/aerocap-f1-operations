"""
tests/test_scheduler.py
Unit tests for Test Operations Coordination and Bottleneck Analysis
"""

import pandas as pd
from datetime import datetime, timedelta
from src.scheduler import TestOperationsScheduler


def test_scheduler_conflict_detection():
    scheduler = TestOperationsScheduler()
    ref_date = datetime(2026, 6, 1, 8, 0)
    
    # Test session scheduled in 2 days
    df_tests = pd.DataFrame([
        {
            "test_id": 1,
            "test_reference": "TEST-DYN-01",
            "facility_id": "DYN-01",
            "scheduled_start": (ref_date + timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
            "scheduled_end": (ref_date + timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
            "actual_status": "Scheduled",
            "critical_part_id": 10
        }
    ])

    # Part requires 5 days lead time -> CONFLICT (Slip of 3 days)
    df_parts = pd.DataFrame([
        {
            "part_id": 10,
            "part_number": "W16-CAMSHAFT-01",
            "revision": "Rev B",
            "lead_time_days": 5,
            "unit_cost_gbp": 45000.0,
            "is_critical_path": 1
        }
    ])

    res = scheduler.evaluate_schedule_feasibility(df_tests, df_parts, reference_date=ref_date)
    assert res["blocked_tests_count"] == 1
    assert res["total_idle_loss_gbp"] > 0
    conflict = res["conflicts_df"].iloc[0]
    assert conflict["part_number"] == "W16-CAMSHAFT-01"
    assert conflict["slip_days"] == 3.0
