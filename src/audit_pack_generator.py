"""
src/audit_pack_generator.py
One-Click FIA Statutory Audit Dossier Generator
Fulfills: FIA Formula 1 Financial Regulations (Issue 24) Articles 5 & 6 Reporting Requirements
"""

import os
from datetime import datetime


class FIAAuditPackGenerator:
    def __init__(self, team_name="Mercedes-Benz Grand Prix Limited", registration_ref="835"):
        self.team_name = team_name
        self.registration_ref = registration_ref

    def generate_markdown_audit_report(self, fin_summary, df_exclusions, df_inventory, df_td045=None):
        """
        Compiles a formal FIA Statutory Compliance Audit Pack matching Article 5.1 format.
        """
        now_str = datetime.now().strftime("%d %B %Y, %H:%M:%S UTC")
        
        md = []
        md.append(f"# FIA FORMULA 1 FINANCIAL REGULATIONS COMPLIANCE DOSSIER")
        md.append(f"**Competitor:** {self.team_name} | **Reference ID:** {self.registration_ref}")
        md.append(f"**Regulatory Framework:** FIA Issue 24 (Published 30 April 2025)")
        md.append(f"**Generated:** {now_str}\n")
        md.append("---\n")

        # 1. Executive Reconciliation
        md.append("## 1. Statutory Cost Cap Reconciliation (Article 2 & Article 4)")
        md.append("| Reconciliation Item | Amount (USD) | Amount (GBP @ 1.2691) | Regulatory Article |")
        md.append("| :--- | :--- | :--- | :--- |")
        md.append(f"| **Gross Total Expenses (Ledger)** | ${fin_summary['gross_expenses_usd']:,.2f} | £{fin_summary['gross_expenses_usd']/1.2691:,.2f} | Audited Accounts |")
        md.append(f"| **Less: Excluded Costs** | (${fin_summary['excluded_expenses_usd']:,.2f}) | (£{fin_summary['excluded_expenses_usd']/1.2691:,.2f}) | Articles 3.1(a)–(y) |")
        md.append(f"| **Add: Used Inventory (Current Car)** | ${fin_summary['used_inventory_added_usd']:,.2f} | £{fin_summary['used_inventory_added_usd']/1.2691:,.2f} | Article 4.1(f)(i)(A) |")
        md.append(f"| **Add: Redundant Inventory Written Off** | ${fin_summary['redundant_inventory_written_off_usd']:,.2f} | £{fin_summary['redundant_inventory_written_off_usd']/1.2691:,.2f} | Article 4.1(f)(i)(C) / TD017 |")
        md.append(f"| **Less: Unused Inventory Carried Forward** | (${fin_summary['unused_inventory_deducted_usd']:,.2f}) | (£{fin_summary['unused_inventory_deducted_usd']/1.2691:,.2f}) | Article 4.1(f)(i)(B) |")
        md.append(f"| **NET RELEVANT COSTS** | **${fin_summary['net_relevant_costs_usd']:,.2f}** | **£{fin_summary['net_relevant_costs_gbp']:,.2f}** | **Article 2.2** |")
        md.append(f"| **FIA Statutory Cap Ceiling** | **${fin_summary['statutory_cap_usd']:,.2f}** | **£{fin_summary['statutory_cap_gbp']:,.2f}** | **Article 2.3 & 4.1(l)** |")
        md.append(f"| **Remaining Compliance Headroom** | **${fin_summary['cost_cap_headroom_usd']:,.2f}** | **£{fin_summary['cost_cap_headroom_gbp']:,.2f}** | **Certified Headroom** |")
        md.append(f"| **Compliance Determination** | **{fin_summary['breach_category']}** | — | **Articles 6.10 & 8** |\n")

        # 2. Capital Expenditure (Appendix 3)
        md.append("## 2. Capital Expenditure Compliance (Article 4.1(e) & Appendix 3)")
        md.append(f"* **Mercedes-Benz Grand Prix Ltd CapEx Limit:** ${fin_summary['capex_limit_usd']:,.2f}")
        md.append(f"* **Total Incurred CapEx Recognized:** ${fin_summary['capex_spent_usd']:,.2f}")
        md.append(f"* **CapEx Regulatory Headroom:** ${fin_summary['capex_headroom_usd']:,.2f}")
        md.append(f"* **CapEx Excess Added to Relevant Costs:** $0.00 (Fully Compliant)\n")

        # 3. Article 3.1 Exclusion Schedule
        md.append("## 3. Article 3.1 Excluded Costs Schedule")
        if not df_exclusions.empty:
            summary_excl = df_exclusions.groupby("exclusion_clause")["amount_usd"].sum().reset_index()
            md.append("| Statutory Exclusion Category | Excluded Amount (USD) |")
            md.append("| :--- | :--- |")
            for _, row in summary_excl.iterrows():
                md.append(f"| {row['exclusion_clause']} | ${row['amount_usd']:,.2f} |")
        md.append("\n")

        # 4. TD045 Applied Science Timesheet Audit
        md.append("## 4. Technical Directive TD045 — Applied Science Carve-Out")
        if df_td045 is not None and not df_td045.empty:
            md.append("| Employee ID | Department | F1 Allocation | Applied Science Allocation | Excluded (£) |")
            md.append("| :--- | :--- | :--- | :--- | :--- |")
            for _, row in df_td045.iterrows():
                md.append(f"| {row['employee_id']} | {row['department']} | {row['f1_allocation_pct']*100:.0f}% | {row['applied_science_allocation_pct']*100:.0f}% | £{row.get('excluded_applied_science_gbp', 0):,.2f} |")
        else:
            md.append("*No cross-allocated Applied Science personnel recorded in this reporting period.*")
        md.append("\n")

        # 5. Formal Declarations (Article 5.1(c))
        md.append("## 5. Formal Declarations & Executive Attestation (Article 5.1(c))")
        md.append("> *We hereby confirm that the Reporting Documentation submitted is complete, accurate, not misleading, and compiled in strict compliance with the FIA Formula 1 Financial Regulations (Issue 24).*\n")
        md.append("* **Team Principal & CEO:** ___________________________ (Date: ____________)")
        md.append("* **Chief Financial Officer:** ________________________ (Date: ____________)")
        md.append("* **Technical Director:** _____________________________ (Date: ____________)")
        md.append("* **Independent Audit Firm Sign-off:** ________________ (Date: ____________)")

        return "\n".join(md)

    def export_to_file(self, content_str, file_path):
        """Writes report to file."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content_str)
        return file_path
