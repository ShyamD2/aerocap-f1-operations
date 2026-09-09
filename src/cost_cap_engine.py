"""
src/cost_cap_engine.py
FIA Formula 1 Financial Regulations (Issue 24, 30 April 2025) Compliance Engine
Full implementation of Articles 2, 3, 4, 8, TD017, TD045, and Appendix 3.
"""

import pandas as pd
import numpy as np
from src.config import (
    BASE_COST_CAP_USD,
    STATUTORY_BASE_COMPETITIONS,
    PER_COMPETITION_DELTA_USD,
    SPRINT_DEDUCTION_USD,
    INITIAL_APPLICABLE_RATE_GBP,
    MERCEDES_CAPEX_LIMIT_USD,
    MINOR_OVERSPEND_MAX_PCT
)


class FIACostCapEngine:
    def __init__(self, calendar_races=24, sprint_count=6, exchange_rate_gbp=INITIAL_APPLICABLE_RATE_GBP):
        self.calendar_races = calendar_races
        self.sprint_count = sprint_count
        self.rate_gbp = exchange_rate_gbp
        self.capex_limit_usd = MERCEDES_CAPEX_LIMIT_USD
        self.base_cap_usd = self.calculate_statutory_cap_usd()

    def calculate_statutory_cap_usd(self):
        """
        Article 2.3 & Article 4.1(l):
        Base Cap: $135,000,000 for 21 Competitions.
        +/- $1,800,000 per competition over/under 21.
        Less $300,000 per Sprint Competition held.
        """
        cap = BASE_COST_CAP_USD
        race_delta = self.calendar_races - STATUTORY_BASE_COMPETITIONS
        cap += (race_delta * PER_COMPETITION_DELTA_USD)
        sprint_adjustment = self.sprint_count * SPRINT_DEDUCTION_USD
        return cap - sprint_adjustment

    @property
    def statutory_cap_gbp(self):
        """Statutory Cap in Presentation Currency (GBP) under Article 2.4."""
        return self.base_cap_usd / self.rate_gbp

    def classify_article_3_exclusions(self, row):
        """
        Tags expenses according to Article 3.1 exclusions.
        Returns: (is_excluded: bool, clause_ref: str)
        """
        cost_centre = str(row.get("cost_centre", "")).upper()
        account_desc = str(row.get("account_desc", "")).upper()

        if "MARKETING" in cost_centre or "SPONSORSHIP" in account_desc:
            return True, "Art. 3.1(a) Marketing Activities"
        if "DRIVER_SALARY" in account_desc:
            return True, "Art. 3.1(b) F1 Driver Consideration"
        if "EXCLUDED_PERSON" in account_desc or "TOP_3_EXECUTIVE" in account_desc:
            return True, "Art. 3.1(d) Top 3 Excluded Persons"
        if "HERITAGE" in cost_centre:
            return True, "Art. 3.1(e) Heritage Asset Activities"
        if "INTEREST" in account_desc or "FINANCE_COST" in account_desc:
            return True, "Art. 3.1(f) Finance Costs"
        if "CORPORATE_TAX" in account_desc or "INCOME_TAX" in account_desc:
            return True, "Art. 3.1(g) Corporate Income Tax"
        if "NON_F1" in cost_centre or "APPLIED_SCIENCE" in cost_centre:
            return True, "Art. 3.1(h) Non-F1 Activities (TD045)"
        if "FLIGHT" in account_desc or "HOTEL" in account_desc or "TRAVEL" in cost_centre:
            return True, "Art. 3.1(r) Personnel Travel & Accommodation"
        if "SUSTAINABILITY" in cost_centre or "CARBON_OFFSET" in account_desc or "SOLAR" in account_desc:
            return True, "Art. 3.1(y) Sustainability Initiative Costs"

        return False, "Relevant Cost (Included)"

    def audit_td045_applied_science(self, df_personnel):
        """
        TD045 & Article 3.1(h):
        Audits personnel allocated between F1 and Applied Science (America's Cup, etc.).
        Returns the non-F1 excluded remuneration amount.
        """
        if df_personnel.empty:
            return 0.0, df_personnel

        df = df_personnel.copy()
        df["excluded_applied_science_gbp"] = df["total_remuneration_gbp"] * df["applied_science_allocation_pct"]
        df["f1_relevant_remuneration_gbp"] = df["total_remuneration_gbp"] * df["f1_allocation_pct"]
        total_excluded_td045_gbp = df["excluded_applied_science_gbp"].sum()
        return total_excluded_td045_gbp, df

    def process_compliance_audit(self, df_expenses, df_parts_inventory, df_personnel=None):
        """
        Executes a complete financial audit reconciliation under Issue 24.
        """
        df_exp = df_expenses.copy()

        # 1. Apply Article 3 Exclusions
        classifications = df_exp.apply(self.classify_article_3_exclusions, axis=1)
        df_exp["is_excluded"] = [c[0] for c in classifications]
        df_exp["exclusion_clause"] = [c[1] for c in classifications]

        # Convert GBP <-> USD if missing
        if "amount_gbp" not in df_exp.columns:
            df_exp["amount_gbp"] = df_exp["amount_usd"] / self.rate_gbp
        if "amount_usd" not in df_exp.columns:
            df_exp["amount_usd"] = df_exp["amount_gbp"] * self.rate_gbp

        # 2. General Ledger Totals
        gross_total_usd = df_exp["amount_usd"].sum()
        excluded_expenses_usd = df_exp.loc[df_exp["is_excluded"] == 1, "amount_usd"].sum()

        # 3. TD045 Personnel Exclusion
        excluded_td045_gbp = 0.0
        if df_personnel is not None and not df_personnel.empty:
            excluded_td045_gbp, _ = self.audit_td045_applied_science(df_personnel)
        excluded_td045_usd = excluded_td045_gbp * self.rate_gbp

        # 4. Article 4.1(f) Inventory Recognition (TD017)
        used_inventory_usd = 0.0
        redundant_inventory_usd = 0.0
        unused_inventory_usd = 0.0
        if not df_parts_inventory.empty:
            used_mask = df_parts_inventory["inventory_status"] == "Used"
            redundant_mask = df_parts_inventory["inventory_status"] == "Redundant"
            unused_mask = df_parts_inventory["inventory_status"] == "Unused"
            
            used_inventory_usd = df_parts_inventory.loc[used_mask, "unit_cost_usd"].sum()
            redundant_inventory_usd = df_parts_inventory.loc[redundant_mask, "unit_cost_usd"].sum()
            unused_inventory_usd = df_parts_inventory.loc[unused_mask, "unit_cost_usd"].sum()

        # 5. CapEx Recognition (Appendix 3)
        capex_mask = df_exp["is_capex"] == 1
        total_capex_usd = df_exp.loc[capex_mask, "amount_usd"].sum()
        capex_excess_usd = max(0.0, total_capex_usd - self.capex_limit_usd)

        # 6. Final Net Relevant Costs (Article 4.1)
        operating_relevant_usd = df_exp.loc[(df_exp["is_excluded"] == 0) & (df_exp["is_capex"] == 0), "amount_usd"].sum()
        
        # Relevant Costs = OpEx (Relevant) + Used Inventory + Redundant Inventory + CapEx Excess - TD045 Personnel Carve-Out
        final_relevant_costs_usd = (operating_relevant_usd 
                                    + used_inventory_usd 
                                    + redundant_inventory_usd 
                                    + capex_excess_usd 
                                    - excluded_td045_usd)
        final_relevant_costs_gbp = final_relevant_costs_usd / self.rate_gbp

        # 7. Breach & Sanction Status (Article 8 & 9)
        variance_usd = final_relevant_costs_usd - self.base_cap_usd
        headroom_usd = self.base_cap_usd - final_relevant_costs_usd
        overspend_pct = (variance_usd / self.base_cap_usd) if variance_usd > 0 else 0.0

        if variance_usd <= 0:
            breach_category = "COMPLIANT"
            potential_sanction = "None. Compliance certificate issued by Cost Cap Administration (Art. 6.10(a))."
        elif overspend_pct < MINOR_OVERSPEND_MAX_PCT:
            breach_category = f"MINOR OVERSPEND BREACH ({overspend_pct*100:.2f}%) [Art. 8.10]"
            potential_sanction = "Financial Penalty and/or Minor Sporting Penalty (Points deduction, testing limitation) [Art. 9.1(b)]."
        else:
            breach_category = f"MATERIAL OVERSPEND BREACH ({overspend_pct*100:.2f}%) [Art. 8.12]"
            potential_sanction = "Mandatory Constructors' Championship Points Deduction and Material Sporting Penalties [Art. 9.1(c)]."

        summary = {
            "calendar_races": self.calendar_races,
            "sprint_count": self.sprint_count,
            "statutory_cap_usd": round(self.base_cap_usd, 2),
            "statutory_cap_gbp": round(self.statutory_cap_gbp, 2),
            "gross_expenses_usd": round(gross_total_usd, 2),
            "excluded_expenses_usd": round(excluded_expenses_usd + excluded_td045_usd, 2),
            "td045_applied_science_excluded_usd": round(excluded_td045_usd, 2),
            "used_inventory_added_usd": round(used_inventory_usd, 2),
            "redundant_inventory_written_off_usd": round(redundant_inventory_usd, 2),
            "unused_inventory_deducted_usd": round(unused_inventory_usd, 2),
            "capex_spent_usd": round(total_capex_usd, 2),
            "capex_limit_usd": round(self.capex_limit_usd, 2),
            "capex_headroom_usd": round(self.capex_limit_usd - total_capex_usd, 2),
            "net_relevant_costs_usd": round(final_relevant_costs_usd, 2),
            "net_relevant_costs_gbp": round(final_relevant_costs_gbp, 2),
            "cost_cap_headroom_usd": round(headroom_usd, 2),
            "cost_cap_headroom_gbp": round(headroom_usd / self.rate_gbp, 2),
            "breach_category": breach_category,
            "potential_sanctions": potential_sanction
        }

        return summary, df_exp
