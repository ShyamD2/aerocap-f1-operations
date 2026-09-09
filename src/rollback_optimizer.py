"""
src/rollback_optimizer.py
Upgrade Failure & Trackside Rollback Cost Matrix
Solves: Fast Friday FP2 emergency rollback evaluation under FIA TD017 Redundant Inventory rules.
"""

from src.config import INITIAL_APPLICABLE_RATE_GBP


class RollbackOptimizer:
    def __init__(self, exchange_rate_gbp=INITIAL_APPLICABLE_RATE_GBP):
        self.rate_gbp = exchange_rate_gbp

    def evaluate_upgrade_rollback(self, failed_package_name, units_manufactured, unit_cost_gbp, 
                                  freight_logistics_gbp=65_000.0, salvage_recovery_pct=0.08):
        """
        Calculates the financial impact of rolling back a failed aerodynamic package.
        
        FIA Article 4.1(f)(i)(C) & TD017:
        Failed parts removed from the car and not intended for future use become Redundant Inventories.
        They must be recognized in full as an expense in the reporting period.
        """
        gross_manufacturing_cost = units_manufactured * unit_cost_gbp
        salvage_value_gbp = gross_manufacturing_cost * salvage_recovery_pct
        net_scrap_loss_gbp = gross_manufacturing_cost - salvage_value_gbp
        
        # Total unexpected cost shock (scrap write-off + emergency freight of spares)
        total_rollback_cost_gbp = net_scrap_loss_gbp + freight_logistics_gbp
        total_rollback_cost_usd = total_rollback_cost_gbp * self.rate_gbp

        action_plan = [
            f"1. Tag {units_manufactured}x '{failed_package_name}' units as REDUNDANT INVENTORY under Article 4.1(f) / TD017.",
            f"2. Write off net scrap value of £{net_scrap_loss_gbp:,.2f} immediately against current Full Year Reporting Period.",
            f"3. Authorize £{freight_logistics_gbp:,.2f} for emergency courier charter of previous-spec spares.",
            "4. Free up planned wind tunnel correlation hours for root-cause diagnosis on next Tuesday."
        ]

        return {
            "failed_package": failed_package_name,
            "units_scrapped": units_manufactured,
            "gross_manufacturing_cost_gbp": gross_manufacturing_cost,
            "salvage_recovery_gbp": salvage_value_gbp,
            "net_scrap_loss_gbp": net_scrap_loss_gbp,
            "emergency_freight_gbp": freight_logistics_gbp,
            "total_cost_shock_gbp": total_rollback_cost_gbp,
            "total_cost_shock_usd": total_rollback_cost_usd,
            "fia_inventory_reclassification": "Redundant Inventory (Art. 4.1(f)(i)(C))",
            "operational_recovery_steps": action_plan
        }
