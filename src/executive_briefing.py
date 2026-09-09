"""
src/executive_briefing.py
Brackley Operations Executive Briefing Generator
Synthesizes multi-physics telemetry, rig OEE, and statutory cost cap data
into military-grade decision briefings for the Team Principal and CFO.
"""

from typing import Dict, Any
from datetime import datetime, timezone


class ExecutiveBriefingGenerator:
    """
    Generates formal executive engineering and operational debriefs
    for Mercedes-AMG PETRONAS Formula One Team leadership.
    """

    @staticmethod
    def generate_memo(
        session_name: str,
        cci: float,
        gate3_locked: bool,
        sunk_cost_saved_gbp: float,
        certified_headroom_gbp: float,
        statutory_cap_gbp: float,
        blocked_rig_count: int,
        cell_oee_pct: float,
        active_upgrade_name: str = "Spec-B Venturi Floor"
    ) -> Dict[str, str]:
        """
        Creates a high-level executive debrief memo formatted for C-suite presentation.
        """
        now_str = datetime.now(timezone.utc).strftime("%d %b %Y | %H:%M UTC")
        
        status_label = "CRITICAL SPEND FREEZE" if gate3_locked else "NOMINAL // UPGRADES RELEASED"
        headroom_pct = (certified_headroom_gbp / statutory_cap_gbp) * 100.0 if statutory_cap_gbp > 0 else 0.0
        
        # 1. Executive Headline
        if gate3_locked:
            headline = (
                f"STAGE GATE 3 AUTOCLAVE SPEND LOCKED: £{sunk_cost_saved_gbp:,.2f} protected from unverified carbon layups. "
                f"Correlation index at {cci:.2f} (< 0.85). Certified headroom remains £{certified_headroom_gbp/1e6:.2f}M ({headroom_pct:.1f}%)."
            )
        else:
            headline = (
                f"CORRELATION NOMINAL (CCI {cci:.2f}): {active_upgrade_name} released to autoclave manufacturing. "
                f"Statutory headroom certified at £{certified_headroom_gbp/1e6:.2f}M ({headroom_pct:.1f}%)."
            )

        # 2. Action Directives
        if gate3_locked:
            directives = (
                f"1. **Aero Department**: Reallocate 35 GPU-hours of CFD allotment immediately to floor-edge vortex generators.\n"
                f"2. **Composite Manufacturing**: Hold Autoclave Cell #3 cycle. Do not cure prepreg tooling until Gate 3 authorization.\n"
                f"3. **Race Engineering**: Impose dynamic ride-height floor threshold of 16.0mm minimum during high-speed FP2 straight runs."
            )
        else:
            directives = (
                f"1. **Composite Manufacturing**: Proceed with 4-set floor carbon layup cycle for European leg deployment.\n"
                f"2. **7-Post Rig Operations**: Schedule 12-hour high-frequency shaker verification Thursday 18:00 UTC.\n"
                f"3. **Financial Operations**: Register £{sunk_cost_saved_gbp:,.2f} variance in TD017 inventory reconciliation ledger."
            )

        # 3. Full Markdown Memo
        markdown_memo = f"""
# MERCEDES-AMG PETRONAS FORMULA ONE TEAM
### **BRACKLEY OPERATIONS ROOM // EXECUTIVE STRATEGY BRIEFING**
**Classification**: RESTRICTED // EXECUTIVE BOARD DISTRIBUTION ONLY  
**Date & Timestamp**: {now_str}  
**Reference**: OPS-DEBRIEF-{session_name.upper().replace(' ', '-')}-2026  
**Addressees**: Toto Wolff (Team Principal & CEO), Chief Financial Officer, Technical Director  

---

### **1. OPERATIONAL STATUS: {status_label}**
{headline}

---

### **2. AERODYNAMIC CORRELATION & TRACK COUPLING**
* **Correlation Confidence Index (CCI)**: **{cci:.2f}** (Statutory Release Gate Threshold: >= 0.85)
* **Underfloor Detachment Risk**: {'CRITICAL STALL CLIFF DETECTED (< 15.2mm)' if gate3_locked else 'NOMINAL ATTACHED VENTURI SUCTION'}
* **Stage Gate 3 Interceptor Action**: {'LOCKED (Autoclave Cycle Suspended)' if gate3_locked else 'RELEASED (Authorized for Layup)'}
* **Sunk Tooling Capital Protected**: **£{sunk_cost_saved_gbp:,.2f}** (FIA Article 2.2 / TD017 Redundant Scrap Avoided)

---

### **3. STATUTORY COST CAP HEALTH (FIA ISSUE 24)**
* **Statutory Baseline Ceiling**: **£{statutory_cap_gbp/1e6:.2f}M** ($138.6M @ 1.2691 FX)
* **Certified Remaining Headroom**: **£{certified_headroom_gbp/1e6:.2f}M** ({headroom_pct:.1f}% Buffer)
* **Breach Risk Level**: {'LOW / DEFENSIVE' if certified_headroom_gbp > 5e6 else 'ELEVATED / PRUDENT'}
* **TD017 Redundant Inventory Write-Off Impact**: £0.00 (Zero unapproved floors scrapped)

---

### **4. FACTORY TEST CELLS & RIG OPERATIONS**
* **Active Rig Availability**: {7 - blocked_rig_count} / 7 Test Cells Active
* **Session Holds / Resource Locks**: {blocked_rig_count} Hold(s) Enforced
* **Overall Equipment Effectiveness (OEE)**: **{cell_oee_pct:.1f}%**
* **Primary Facility Critical Path**: Autoclave Cell #3 & 60% Scale Wind Tunnel Rolling Road

---

### **5. MANDATORY C-SUITE DIRECTIVES**
{directives}

---
*AEROCAP v2.4 Automated Intelligence Engine • Brackley F1 Operations Room*
"""
        return {
            "headline": headline,
            "directives": directives,
            "markdown_memo": markdown_memo.strip()
        }
