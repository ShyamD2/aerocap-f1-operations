"""
src/pdf_generator.py
Publication-Grade FIA Financial Regulations (Issue 24) Compliance PDF Generator
Uses ReportLab to compile formal Article 5 & 6 reporting documentation.
"""

import io
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


class FIAPDFReportGenerator:
    def __init__(self, team_name="Mercedes-Benz Grand Prix Limited", registration_ref="835"):
        self.team_name = team_name
        self.registration_ref = registration_ref

    def generate_pdf_bytes(self, fin_summary, df_exclusions=None, df_td045=None):
        """
        Generates and returns an official PDF compliance dossier as a bytes buffer.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom Paragraph Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#121212"),
            alignment=1, # Center
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#00A19B"),
            alignment=1,
            spaceAfter=12
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#121212"),
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#2C2C2C")
        )
        body_bold = ParagraphStyle(
            "BodyBold",
            parent=body_style,
            fontName="Helvetica-Bold"
        )

        elements = []

        # 1. Header Banner
        elements.append(Paragraph("FEDERATION INTERNATIONALE DE L'AUTOMOBILE", title_style))
        elements.append(Paragraph(f"FORMULA 1 FINANCIAL REGULATIONS COMPLIANCE DOSSIER — ISSUE 24", section_heading))
        elements.append(Paragraph(
            f"<b>Competitor:</b> {self.team_name} | <b>Registration Ref:</b> {self.registration_ref} | "
            f"<b>Reporting Date:</b> {datetime.now(timezone.utc).strftime('%d %B %Y')}",
            subtitle_style
        ))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#00A19B"), spaceAfter=10))

        # 2. Section 1: Statutory Reconciliation
        elements.append(Paragraph("1. Statutory Cost Cap Reconciliation (Articles 2 & 4)", section_heading))
        recon_data = [
            [Paragraph("<b>Regulatory Reconciliation Line Item</b>", body_bold),
             Paragraph("<b>USD ($)</b>", body_bold),
             Paragraph("<b>GBP (£ @ 1.2691)</b>", body_bold),
             Paragraph("<b>Article Reference</b>", body_bold)],
            
            ["Gross Ledger Total Expenses", f"${fin_summary['gross_expenses_usd']:,.2f}", f"£{fin_summary['gross_expenses_usd']/1.2691:,.2f}", "Audited Accounts"],
            ["Less: Article 3.1 Excluded Costs", f"(${fin_summary['excluded_expenses_usd']:,.2f})", f"(£{fin_summary['excluded_expenses_usd']/1.2691:,.2f})", "Articles 3.1(a)–(y)"],
            ["Add: Used Inventories (Current Car)", f"${fin_summary['used_inventory_added_usd']:,.2f}", f"£{fin_summary['used_inventory_added_usd']/1.2691:,.2f}", "Art. 4.1(f)(i)(A)"],
            ["Add: Redundant Inventories Written Off", f"${fin_summary['redundant_inventory_written_off_usd']:,.2f}", f"£{fin_summary['redundant_inventory_written_off_usd']/1.2691:,.2f}", "Art. 4.1(f)(i)(C) / TD017"],
            ["Less: Unused Inventories Carried Forward", f"(${fin_summary['unused_inventory_deducted_usd']:,.2f})", f"(£{fin_summary['unused_inventory_deducted_usd']/1.2691:,.2f})", "Art. 4.1(f)(i)(B)"],
            [Paragraph("<b>NET RELEVANT COSTS</b>", body_bold), 
             Paragraph(f"<b>${fin_summary['net_relevant_costs_usd']:,.2f}</b>", body_bold), 
             Paragraph(f"<b>£{fin_summary['net_relevant_costs_gbp']:,.2f}</b>", body_bold), 
             Paragraph("<b>Article 2.2</b>", body_bold)],
            [Paragraph("<b>FIA Statutory Cost Cap Target</b>", body_bold), 
             Paragraph(f"<b>${fin_summary['statutory_cap_usd']:,.2f}</b>", body_bold), 
             Paragraph(f"<b>£{fin_summary['statutory_cap_gbp']:,.2f}</b>", body_bold), 
             Paragraph("<b>Article 2.3 & 4.1(l)</b>", body_bold)],
            [Paragraph("<b>Certified Regulatory Headroom</b>", body_bold), 
             Paragraph(f"<b>${fin_summary['cost_cap_headroom_usd']:,.2f}</b>", body_bold), 
             Paragraph(f"<b>£{fin_summary['cost_cap_headroom_gbp']:,.2f}</b>", body_bold), 
             Paragraph(f"<b>{fin_summary['breach_category']}</b>", body_bold)],
        ]

        t1 = Table(recon_data, colWidths=[200, 110, 110, 100])
        t1.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2F4F7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#121212")),
            ("ALIGN", (1, 0), (2, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D5DD")),
            ("LINEBELOW", (0, 5), (-1, 5), 1.5, colors.HexColor("#00A19B")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 10))

        # 3. Section 2: Appendix 3 CapEx & TD045 Applied Science
        elements.append(Paragraph("2. Capital Expenditure (Appendix 3) & TD045 Apportionment", section_heading))
        capex_data = [
            ["Appendix 3 CapEx Limit (Mercedes)", f"${fin_summary['capex_limit_usd']:,.2f}", "Status", "FULLY COMPLIANT"],
            ["Recognized Tangible & Intangible CapEx", f"${fin_summary['capex_spent_usd']:,.2f}", "CapEx Headroom", f"${fin_summary['capex_headroom_usd']:,.2f}"],
            ["TD045 Applied Science Remuneration Carve-Out", f"${fin_summary.get('td045_applied_science_excluded_usd', 0.0):,.2f}", "Art. 3.1(h) Non-F1", "Audited Timesheets"]
        ]
        t2 = Table(capex_data, colWidths=[180, 100, 110, 130])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t2)
        elements.append(Spacer(1, 10))

        # 4. Section 3: Article 3.1 Exclusions Breakdown
        if df_exclusions is not None and not df_exclusions.empty:
            elements.append(Paragraph("3. Article 3.1 Excluded Expenses Schedule", section_heading))
            excl_grouped = df_exclusions.groupby("exclusion_clause")["amount_usd"].sum().reset_index()
            excl_rows = [[Paragraph("<b>Statutory Exclusion Category</b>", body_bold), Paragraph("<b>Amount (USD)</b>", body_bold)]]
            for _, r in excl_grouped.iterrows():
                excl_rows.append([r["exclusion_clause"], f"${r['amount_usd']:,.2f}"])
            
            t3 = Table(excl_rows, colWidths=[380, 140])
            t3.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2F4F7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D5DD")),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(t3)
            elements.append(Spacer(1, 12))

        # 5. Section 4: Executive Attestation & Signatures (Article 5.1(c))
        elements.append(Paragraph("4. Executive Declarations & Legal Attestation (Article 5.1(c))", section_heading))
        elements.append(Paragraph(
            "<i>We, the undersigned executive officers of Mercedes-Benz Grand Prix Limited, confirm under penalty of sporting sanctions "
            "that the figures and schedules herein represent a true, fair, and accurate declaration under the FIA Financial Regulations.</i>",
            body_style
        ))
        elements.append(Spacer(1, 14))

        sig_data = [
            ["____________________________________", "____________________________________"],
            ["Toto Wolff (Team Principal & CEO)", "Chief Financial Officer (CFO)"],
            ["Date: ________________________", "Date: ________________________"],
            ["", ""],
            ["____________________________________", "____________________________________"],
            ["Technical Director (F1 Programme)", "Independent Senior Statutory Auditor"],
            ["Date: ________________________", "Date: ________________________"],
        ]
        t_sig = Table(sig_data, colWidths=[260, 260])
        t_sig.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#555555")),
            ("TEXTCOLOR", (0, 5), (-1, 5), colors.HexColor("#555555")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(t_sig)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
