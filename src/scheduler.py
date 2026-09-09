"""
src/scheduler.py
Test Operations Coordination, Critical Path Analysis, & Facility Scheduling
Solves: Prevention of idle test cells (DYN-01, RIG-02, WT-01) due to part delivery bottlenecks.
"""

from datetime import datetime
import pandas as pd
import numpy as np
from src.config import FACILITY_HOURLY_COSTS_GBP


class TestOperationsScheduler:
    __test__ = False
    def __init__(self, hourly_costs_gbp=None):
        self.hourly_costs = hourly_costs_gbp or FACILITY_HOURLY_COSTS_GBP

    def evaluate_schedule_feasibility(self, df_tests, df_parts, reference_date=None):
        """
        Cross-references test runs against component lead times.
        Identifies blocked test cells and calculates idle facility financial losses.
        """
        ref_date = pd.to_datetime(reference_date) if reference_date else pd.to_datetime(datetime.now())
        
        merged = df_tests.merge(
            df_parts[["part_id", "part_number", "revision", "lead_time_days", "unit_cost_gbp", "is_critical_path"]],
            left_on="critical_part_id",
            right_on="part_id",
            how="left"
        )

        merged["scheduled_start_dt"] = pd.to_datetime(merged["scheduled_start"])
        merged["scheduled_end_dt"] = pd.to_datetime(merged["scheduled_end"])
        merged["duration_hours"] = (merged["scheduled_end_dt"] - merged["scheduled_start_dt"]).dt.total_seconds() / 3600.0

        # Part Ready Date = Ref Date + Lead Time Days
        merged["part_ready_dt"] = ref_date + pd.to_timedelta(merged["lead_time_days"].fillna(0), unit="D")

        # Conflict Detection: Part arrives after test scheduled start
        merged["is_blocked"] = (merged["part_ready_dt"] > merged["scheduled_start_dt"]) & (merged["actual_status"] != "Completed")
        
        # Calculate days of slip
        merged["slip_days"] = (merged["part_ready_dt"] - merged["scheduled_start_dt"]).dt.total_seconds() / (24 * 3600.0)
        merged["slip_days"] = merged["slip_days"].apply(lambda x: max(0.0, round(x, 1)))

        # Calculate Idle Cost = Blocked Duration Hours * Facility Hourly Rate
        merged["hourly_rate_gbp"] = merged["facility_id"].map(self.hourly_costs).fillna(1500.0)
        merged["potential_idle_cost_gbp"] = np.where(
            merged["is_blocked"],
            merged["duration_hours"] * merged["hourly_rate_gbp"],
            0.0
        )

        conflicts = merged[merged["is_blocked"]].copy()
        total_idle_loss_gbp = conflicts["potential_idle_cost_gbp"].sum()

        return {
            "total_tests": len(merged),
            "blocked_tests_count": len(conflicts),
            "total_idle_loss_gbp": round(total_idle_loss_gbp, 2),
            "detailed_schedule": merged,
            "conflicts_df": conflicts[[
                "test_id", "test_reference", "facility_id", "part_number", "revision",
                "scheduled_start", "part_ready_dt", "slip_days", "potential_idle_cost_gbp"
            ]]
        }

    def process_engineering_change_order(self, part_number, old_rev, new_rev, wip_completion_pct, unit_cost_gbp, added_lead_time_days):
        """
        Calculates the financial and schedule impact of an in-process Engineering Change Order (ECO).
        """
        wip_scrap_cost_gbp = unit_cost_gbp * wip_completion_pct
        return {
            "part_number": part_number,
            "revision_change": f"{old_rev} -> {new_rev}",
            "wip_completion_pct": wip_completion_pct * 100,
            "wip_scrap_cost_gbp": round(wip_scrap_cost_gbp, 2),
            "schedule_lead_time_penalty_days": added_lead_time_days,
            "recommended_action": (f"Scrap {wip_completion_pct*100:.0f}% machined stock (£{wip_scrap_cost_gbp:,.2f}). "
                                  f"Reschedule downstream dyno slot by +{added_lead_time_days} days.")
        }
