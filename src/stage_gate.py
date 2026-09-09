"""
src/stage_gate.py
Correlation-Gated Financial Spending Release & Authorization Gatekeeper
Protects Mercedes from burning Cost Cap funds on unproven or detached aero concepts.
"""

from src.config import CCI_MIN_GATE3_RELEASE


class StageGateManager:
    def __init__(self, min_cci_for_production=CCI_MIN_GATE3_RELEASE):
        self.min_cci = min_cci_for_production

    def evaluate_gate_release(self, component_code, cci_score, planned_tooling_cost_gbp, planned_autoclave_hours):
        """
        Determines whether manufacturing spending is released or blocked.
        
        Gate 1: Aero Concept & CFD (Autonomous)
        Gate 2: Rapid Prototyping & Wind Tunnel Model Shop (Autonomous)
        Gate 3: Full-Scale Composite Tooling & Autoclave Manufacture (Correlation-Gated)
        """
        is_authorized = cci_score >= self.min_cci
        
        if is_authorized:
            decision = "RELEASE_AUTHORIZED"
            risk_classification = "LOW_RISK"
            funds_committed_gbp = planned_tooling_cost_gbp
            funds_protected_gbp = 0.0
            autoclave_hours_allocated = planned_autoclave_hours
            message = (f"Gate 3 Passed (CCI: {cci_score:.3f} >= {self.min_cci}). "
                       f"Authorized £{planned_tooling_cost_gbp:,.2f} and {planned_autoclave_hours}h autoclave capacity.")
        else:
            decision = "PRODUCTION_LOCKED"
            risk_classification = "CRITICAL_CORRELATION_DEFICIT"
            funds_committed_gbp = 0.0
            # Sunk cost avoided = full production run cost
            funds_protected_gbp = planned_tooling_cost_gbp
            autoclave_hours_allocated = 0.0
            deficit_pct = ((self.min_cci - cci_score) / self.min_cci) * 100
            message = (f"Gate 3 BLOCKED: CCI {cci_score:.3f} is {deficit_pct:.1f}% below minimum threshold ({self.min_cci}). "
                       f"Prevented £{funds_protected_gbp:,.2f} in potential scrap and conserved {planned_autoclave_hours}h autoclave time.")

        return {
            "component_code": component_code,
            "cci_score": cci_score,
            "decision": decision,
            "risk_classification": risk_classification,
            "funds_committed_gbp": funds_committed_gbp,
            "funds_protected_gbp": funds_protected_gbp,
            "autoclave_hours_allocated": autoclave_hours_allocated,
            "gatekeeper_message": message
        }
