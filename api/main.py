"""
api/main.py
FastAPI High-Performance REST API Bridge for F1-OpsCorrelate
Serves calculations to the React UI and external webhooks.
"""

import os
import sys
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import load_table
from src.cost_cap_engine import FIACostCapEngine
from src.pareto_optimizer import ParetoUpgradeOptimizer
from src.fastf1_telemetry import F1TelemetryAnalyzer
from src.pdf_generator import FIAPDFReportGenerator

app = FastAPI(
    title="Mercedes-AMG F1 OpsCorrelate API",
    description="REST backend providing telemetry, correlation, and FIA Cost Cap compliance data.",
    version="2.0.0"
)

# Enable CORS for React frontend (localhost:3000 / localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ONLINE", "team": "Mercedes-AMG PETRONAS F1 Team", "department": "Operations (835)"}


@app.get("/api/cost-cap-summary")
def get_cost_cap_summary(races: int = 24, sprints: int = 6):
    df_parts = load_table("dim_parts")
    df_expenses = load_table("fact_expenses")
    df_personnel = load_table("dim_personnel_td045")
    
    engine = FIACostCapEngine(calendar_races=races, sprint_count=sprints)
    summary, _ = engine.process_compliance_audit(df_expenses, df_parts, df_personnel)
    return summary


@app.get("/api/pareto-upgrades")
def get_pareto_upgrades():
    df_upgrades = load_table("candidate_upgrades")
    optimizer = ParetoUpgradeOptimizer()
    res = optimizer.identify_pareto_frontier(df_upgrades)
    return res.to_dict(orient="records")


@app.get("/api/telemetry/silverstone")
def get_silverstone_telemetry():
    analyzer = F1TelemetryAnalyzer(driver="RUS", grand_prix="Silverstone", year=2024)
    df = analyzer.load_telemetry_lap(use_live_api=False)
    return df.to_dict(orient="records")


@app.get("/api/download-audit-pdf")
def download_audit_pdf(races: int = 24, sprints: int = 6):
    df_parts = load_table("dim_parts")
    df_expenses = load_table("fact_expenses")
    df_personnel = load_table("dim_personnel_td045")
    
    engine = FIACostCapEngine(calendar_races=races, sprint_count=sprints)
    summary, processed_exp = engine.process_compliance_audit(df_expenses, df_parts, df_personnel)
    
    pdf_gen = FIAPDFReportGenerator()
    df_excl = processed_exp[processed_exp["is_excluded"] == 1]
    pdf_bytes = pdf_gen.generate_pdf_bytes(summary, df_excl, df_personnel)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=FIA_Cost_Cap_Mercedes_Issue24.pdf"}
    )
