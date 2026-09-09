"""
src/season_roadmap.py
Season Roadmap & Strategic "What-If" Upgrade/Accident Simulator
Calculates cumulative statutory cost cap burn across 24 Grands Prix.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from src.config import BASE_COST_CAP_USD, INITIAL_APPLICABLE_RATE_GBP


class SeasonRoadmapEngine:
    """
    Simulates season-long financial burn and performance trajectory across 24 Grands Prix,
    incorporating candidate upgrade deployments and stochastic crash damage.
    """

    RACES = [
        "Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami",
        "Emilia Romagna", "Monaco", "Canada", "Spain", "Austria", "Great Britain",
        "Hungary", "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore",
        "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
    ]

    AVAILABLE_UPGRADES = [
        {
            "id": "UPG_JPN_FLOOR_EDGE",
            "name": "Japan GP Floor Edge Winglet",
            "race_idx": 4, # Japan
            "cost_gbp": 220000.0,
            "laptime_delta_ms": -60.0,
            "stage_gate_passed": True,
            "category": "Aerodynamics"
        },
        {
            "id": "UPG_ESP_SPEC_B_FLOOR",
            "name": "Spain GP Spec-B Venturi Floor",
            "race_idx": 10, # Spain
            "cost_gbp": 450000.0,
            "laptime_delta_ms": -150.0,
            "stage_gate_passed": True,
            "category": "Floor & Diffuser"
        },
        {
            "id": "UPG_GBR_SIDEPOD_UNDERCUT",
            "name": "Silverstone Sidepod Undercut",
            "race_idx": 12, # Great Britain
            "cost_gbp": 320000.0,
            "laptime_delta_ms": -90.0,
            "stage_gate_passed": True,
            "category": "Bodywork"
        },
        {
            "id": "UPG_BEL_LOW_DRAG_WING",
            "name": "Spa Low-Drag Beam Wing",
            "race_idx": 14, # Belgium
            "cost_gbp": 190000.0,
            "laptime_delta_ms": -55.0,
            "stage_gate_passed": True,
            "category": "Rear Wing"
        },
        {
            "id": "UPG_USA_THROAT_EVO",
            "name": "Austin Venturi Throat Evolution",
            "race_idx": 19, # United States
            "cost_gbp": 380000.0,
            "laptime_delta_ms": -110.0,
            "stage_gate_passed": True,
            "category": "Floor & Diffuser"
        }
    ]

    CRASH_SCENARIOS = {
        "Clean Season (No Major Damage)": {
            "race_idx": None,
            "cost_gbp": 0.0,
            "description": "Baseline component attrition covered by standard operational spares budget."
        },
        "Minor FP1 Impact (Gearbox & Suspension)": {
            "race_idx": 8, # Canada
            "cost_gbp": 420000.0,
            "description": "Wall of Champions contact requiring complete rear suspension and gearbox casing replacement."
        },
        "Catastrophic Turn 1 Multi-Car Chassis Scrappage": {
            "race_idx": 11, # Austria
            "cost_gbp": 1450000.0,
            "description": "Severe primary survival cell puncture requiring complete monocoque and power unit write-off."
        }
    }

    def __init__(self, calendar_races: int = 24, sprint_count: int = 6):
        self.calendar_races = calendar_races
        self.sprint_count = sprint_count
        self.races = self.RACES[:calendar_races]
        
        # Statutory Cost Cap calculation
        race_adj_usd = max(0, self.calendar_races - 21) * 1800000.0
        sprint_deduct_usd = self.sprint_count * 300000.0
        self.statutory_cap_usd = BASE_COST_CAP_USD + race_adj_usd - sprint_deduct_usd
        self.statutory_cap_gbp = self.statutory_cap_usd / INITIAL_APPLICABLE_RATE_GBP

    def simulate_season(
        self,
        active_upgrade_ids: List[str],
        crash_scenario_key: str = "Clean Season (No Major Damage)"
    ) -> Dict[str, Any]:
        """
        Calculates the 24-race cumulative spending progression and remaining headroom.
        """
        n_races = len(self.races)
        
        # Baseline operational spend per race (travel, logistics, base manufacturing)
        # Mercedes targets ~£96M baseline operational spend before upgrades
        base_per_race_gbp = 96000000.0 / n_races
        
        # Array of incremental costs per race
        incremental_upgrade_costs = np.zeros(n_races)
        incremental_laptime_gains = np.zeros(n_races)
        
        for upg in self.AVAILABLE_UPGRADES:
            if upg["id"] in active_upgrade_ids:
                idx = min(upg["race_idx"] - 1, n_races - 1)
                incremental_upgrade_costs[idx] += upg["cost_gbp"]
                incremental_laptime_gains[idx:] += upg["laptime_delta_ms"]

        # Apply crash scenario
        crash_info = self.CRASH_SCENARIOS.get(crash_scenario_key, self.CRASH_SCENARIOS["Clean Season (No Major Damage)"])
        crash_cost_gbp = crash_info["cost_gbp"]
        if crash_info["race_idx"] is not None and crash_cost_gbp > 0:
            c_idx = min(crash_info["race_idx"] - 1, n_races - 1)
            incremental_upgrade_costs[c_idx] += crash_cost_gbp

        # Compute cumulative spend
        race_by_race_spend = base_per_race_gbp + incremental_upgrade_costs
        cumulative_spend_gbp = np.cumsum(race_by_race_spend)
        cumulative_spend_usd = cumulative_spend_gbp * INITIAL_APPLICABLE_RATE_GBP
        
        # Headroom progression
        remaining_headroom_gbp = self.statutory_cap_gbp - cumulative_spend_gbp
        remaining_headroom_usd = self.statutory_cap_usd - cumulative_spend_usd
        
        # Final year-end metrics
        total_upgrade_spend_gbp = sum(
            upg["cost_gbp"] for upg in self.AVAILABLE_UPGRADES if upg["id"] in active_upgrade_ids
        )
        total_laptime_gain_ms = abs(float(incremental_laptime_gains[-1])) if len(incremental_laptime_gains) > 0 else 0.0
        final_headroom_gbp = float(remaining_headroom_gbp[-1])
        final_headroom_usd = float(remaining_headroom_usd[-1])
        
        cost_per_ms_overall = (
            total_upgrade_spend_gbp / total_laptime_gain_ms if total_laptime_gain_ms > 0 else 0.0
        )
        
        # Compliance state
        is_breach = final_headroom_gbp < 0
        danger_zone = 0 <= final_headroom_gbp < 2000000.0

        df_trajectory = pd.DataFrame({
            "Race_Number": np.arange(1, n_races + 1),
            "Grand_Prix": self.races,
            "Race_Spend_GBP": race_by_race_spend,
            "Cumulative_Spend_GBP": cumulative_spend_gbp,
            "Cumulative_Spend_USD": cumulative_spend_usd,
            "Remaining_Headroom_GBP": remaining_headroom_gbp,
            "Remaining_Headroom_USD": remaining_headroom_usd,
            "Cumulative_Laptime_Gain_ms": np.abs(incremental_laptime_gains),
            "Cap_Limit_GBP": np.full(n_races, self.statutory_cap_gbp)
        })

        return {
            "trajectory_df": df_trajectory,
            "total_upgrade_spend_gbp": total_upgrade_spend_gbp,
            "crash_cost_gbp": crash_cost_gbp,
            "final_headroom_gbp": final_headroom_gbp,
            "final_headroom_usd": final_headroom_usd,
            "total_laptime_gain_ms": total_laptime_gain_ms,
            "cost_per_ms_overall": cost_per_ms_overall,
            "is_breach": is_breach,
            "danger_zone": danger_zone,
            "statutory_cap_gbp": self.statutory_cap_gbp,
            "statutory_cap_usd": self.statutory_cap_usd
        }
