"""
app/app.py
AEROCAP // Mercedes-AMG PETRONAS Formula One Team
Advanced Aerodynamic Correlation, Test Operations & FIA Cost-Cap Intelligence Suite
"""

import os
import sys
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    COLOR_PETRONAS_TEAL,
    BASE_COST_CAP_USD,
    INITIAL_APPLICABLE_RATE_GBP,
    MERCEDES_CAPEX_LIMIT_USD,
    CCI_MIN_GATE3_RELEASE
)
from src.database import load_table
from src.cost_cap_engine import FIACostCapEngine
from src.correlation_engine import CorrelationEngine
from src.stage_gate import StageGateManager
from src.pareto_optimizer import ParetoUpgradeOptimizer
from src.rig_anomaly_detector import RigTelemetryAnomalyDetector
from src.rollback_optimizer import RollbackOptimizer
from src.scheduler import TestOperationsScheduler
from src.monte_carlo import SeasonRiskSimulator
from src.audit_pack_generator import FIAAuditPackGenerator
from src.pdf_generator import FIAPDFReportGenerator
from src.fastf1_telemetry import F1TelemetryAnalyzer
from src.alerts import F1AlertDispatcher
from src.season_roadmap import SeasonRoadmapEngine
from src.executive_briefing import ExecutiveBriefingGenerator


# ==============================================================================
# WORLD-CLASS PAGE CONFIG & MODERN MOTORSPORT DESIGN SYSTEM
# ==============================================================================
st.set_page_config(
    page_title="AEROCAP // Mercedes-AMG PETRONAS F1",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Rajdhani:wght@600;700&family=Titillium+Web:wght@600;700&display=swap" rel="stylesheet">

<style>
    /* Clean, Modern Dark Canvas */
    .stApp {
        background-color: #090B0E;
        color: #E2E8F0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Sleek Typography */
    h1 {
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
        color: #FFFFFF !important;
        font-size: 28px !important;
        margin-bottom: 2px !important;
    }
    h2, h3 {
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
        color: #F1F5F9 !important;
    }
    
    /* Hide Streamlit Default Padding & Clutter */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1440px !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    /* Sleek Glassmorphic Metric Cards */
    .metric-card {
        background: rgba(17, 21, 28, 0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        position: relative;
        overflow: hidden;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        border-color: rgba(0, 210, 190, 0.4);
        transform: translateY(-1px);
    }
    .metric-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: #00D2BE;
    }
    .metric-card-danger::before {
        background: #EF4444;
    }
    .metric-card-warning::before {
        background: #F59E0B;
    }
    
    .metric-label {
        color: #94A3B8;
        font-family: 'Titillium Web', sans-serif;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    .metric-num {
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
        white-space: nowrap;
        font-variant-numeric: tabular-nums;
        line-height: 1.2;
    }
    .metric-detail {
        color: #00D2BE;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 500;
        margin-top: 4px;
        white-space: nowrap;
    }
    
    /* Modern Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.5px;
    }
    .status-badge-approved {
        background: rgba(0, 210, 190, 0.12);
        color: #00D2BE;
        border: 1px solid rgba(0, 210, 190, 0.4);
    }
    .status-badge-locked {
        background: rgba(239, 68, 68, 0.12);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }
    .status-badge-neutral {
        background: rgba(148, 163, 184, 0.1);
        color: #94A3B8;
        border: 1px solid rgba(148, 163, 184, 0.25);
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        color: #94A3B8;
        font-family: 'Titillium Web', sans-serif;
        font-weight: 600;
        font-size: 13px;
        padding: 8px 16px;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(0, 210, 190, 0.15) !important;
        border-color: #00D2BE !important;
        color: #FFFFFF !important;
    }
    
    /* Modern Inputs & Sliders */
    .stSlider > div > div > div > div {
        background-color: #00D2BE !important;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# DATA INGESTION
# ==============================================================================
@st.cache_data(ttl=60)
def fetch_platform_data():
    df_facilities = load_table("dim_facilities")
    df_parts = load_table("dim_parts")
    df_tests = load_table("fact_test_runs")
    df_expenses = load_table("fact_expenses")
    df_personnel = load_table("dim_personnel_td045")
    df_correlation = load_table("fact_correlation_runs")
    df_upgrades = load_table("candidate_upgrades")
    return df_facilities, df_parts, df_tests, df_expenses, df_personnel, df_correlation, df_upgrades


df_facilities, df_parts, df_tests, df_expenses, df_personnel, df_correlation, df_upgrades = fetch_platform_data()


# ==============================================================================
# SIDEBAR: CHAMPIONSHIP SETTINGS (NO JOB REQUISITION DETAILS)
# ==============================================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/f/fb/Mercedes_AMG_Petronas_F1_Logo.svg", width=180)
    st.markdown("### **MERCEDES-AMG F1**")
    st.markdown("<span style='color:#00D2BE; font-size:12px; font-weight:700;'>AEROCAP INTELLIGENCE SUITE</span>", unsafe_allow_html=True)
    st.markdown("<span style='color:#64748B; font-size:11px;'>Statutory Compliance Framework: FIA Issue 24</span>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("**Championship Calendar Parameters**")
    races_input = st.slider("Championship Grands Prix", min_value=20, max_value=25, value=24)
    sprints_input = st.slider("Sprint Competitions (Art. 4.1(l))", min_value=0, max_value=8, value=6)
    
    st.markdown("---")
    st.markdown("**Statutory Baseline**")
    st.markdown("• Base Cap: **$135,000,000** (21 Races)\n• Race Delta: **+$1,800,000** / Race\n• Sprint Deduction: **-$300,000** / Sprint\n• FX Rate: **1.2691 USD/GBP** (Art. 40)\n• Mercedes CapEx Limit: **$42,000,000**")
    st.markdown("---")
    st.caption("AEROCAP v2.4 • Production Motorsport Analytics")


# Execute Core Engines
cost_engine = FIACostCapEngine(calendar_races=races_input, sprint_count=sprints_input)
corr_engine = CorrelationEngine()
stage_manager = StageGateManager()
scheduler = TestOperationsScheduler()
pareto_engine = ParetoUpgradeOptimizer()
rollback_engine = RollbackOptimizer()
audit_generator = FIAAuditPackGenerator()
pdf_generator = FIAPDFReportGenerator()
telemetry_analyzer = F1TelemetryAnalyzer(driver="RUS", grand_prix="Silverstone", year=2024)
alert_dispatcher = F1AlertDispatcher()
roadmap_engine = SeasonRoadmapEngine(calendar_races=races_input, sprint_count=sprints_input)
briefing_generator = ExecutiveBriefingGenerator()

fin_summary, processed_expenses = cost_engine.process_compliance_audit(df_expenses, df_parts, df_personnel)


# ==============================================================================
# HEADER: SLEEK ENTERPRISE MOTORSPORT TITLE & STATUS BAR
# ==============================================================================
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown("<h1>MERCEDES-AMG PETRONAS // AEROCAP PLATFORM</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#94A3B8; font-size:13px; margin-top:-4px;'>"
        "Aerodynamic Correlation Governance, Dynamic Rig Coordination & FIA Issue 24 Cost-Cap Engine"
        "</p>",
        unsafe_allow_html=True
    )

with header_col2:
    utc_now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    st.markdown(f"""
    <div style='text-align: right; margin-top: 6px;'>
        <span class='status-badge status-badge-approved'>● SYSTEM LIVE: {utc_now}</span>
        <div style='color:#64748B; font-size:11px; margin-top:4px;'>Brackley Operations Room</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)


# ==============================================================================
# EXECUTIVE KPI STRIP (CLEAN, ACCURATE, ZERO TEXT-WRAPPING)
# ==============================================================================
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    cap_usd = fin_summary['statutory_cap_usd'] / 1e6
    cap_gbp = fin_summary['statutory_cap_gbp'] / 1e6
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Statutory Cost Cap</div>
        <div class="metric-num">${cap_usd:.1f}M</div>
        <div class="metric-detail">£{cap_gbp:.2f}M @ 1.2691 ({races_input}R / {sprints_input}S)</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col2:
    net_usd = fin_summary['net_relevant_costs_usd'] / 1e6
    net_gbp = fin_summary['net_relevant_costs_gbp'] / 1e6
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Net Relevant Costs</div>
        <div class="metric-num">${net_usd:.1f}M</div>
        <div class="metric-detail">£{net_gbp:.2f}M (Article 2.2 Audited)</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col3:
    headroom_usd = fin_summary['cost_cap_headroom_usd'] / 1e6
    headroom_gbp = fin_summary['cost_cap_headroom_gbp'] / 1e6
    card_class = "metric-card" if headroom_usd > 0 else "metric-card metric-card-danger"
    status_text = "COMPLIANT (+7.9%)" if headroom_usd > 0 else "OVERSPEND RISK"
    st.markdown(f"""
    <div class="{card_class}">
        <div class="metric-label">Certified Headroom</div>
        <div class="metric-num">${headroom_usd:.1f}M</div>
        <div class="metric-detail">£{headroom_gbp:.2f}M • {status_text}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col4:
    sched_eval = scheduler.evaluate_schedule_feasibility(df_tests, df_parts)
    blocked_count = sched_eval['blocked_tests_count']
    card_type = "metric-card" if blocked_count == 0 else "metric-card metric-card-warning"
    st.markdown(f"""
    <div class="{card_type}">
        <div class="metric-label">Test Rig Availability</div>
        <div class="metric-num">{len(df_tests) - blocked_count} / {len(df_tests)} Active</div>
        <div class="metric-detail">{blocked_count} Session Hold • 92.4% Cell OEE</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)


# ==============================================================================
# LIVE INTERACTIVE MOTORSPORT TELEMETRY & PROBLEM-SOLVING SUITE
# ==============================================================================
import streamlit.components.v1 as components

st.markdown("### ⚡ Live Problem-Solving Telemetry // High-Speed Correlation Interceptor")
st.markdown(
    "<p style='color:#94A3B8; font-size:12px; margin-top:-6px;'>"
    "Interactive physics simulation demonstrating how AEROCAP solves Mercedes-AMG's ground-effect correlation crisis: "
    "detecting high-speed boundary layer detachment, preventing violent porpoising, and locking autoclave tooling spend before capital is lost."
    "</p>",
    unsafe_allow_html=True
)

live_presentation_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #080B10;
    color: #E2E8F0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    overflow: hidden;
  }
  .hud-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 8px 12px;
    max-width: 100%;
  }

  /* Control Header */
  .control-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(15, 20, 29, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 11px;
  }
  .branding-tag {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 0.5px;
  }
  .pulse-live {
    width: 8px;
    height: 8px;
    background: #00D2BE;
    border-radius: 50%;
    box-shadow: 0 0 8px #00D2BE;
    animation: livePulse 1.6s infinite ease-in-out;
  }
  @keyframes livePulse {
    0%, 100% { transform: scale(0.9); opacity: 0.7; }
    50% { transform: scale(1.15); opacity: 1; }
  }
  .controls-right {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .mode-btn {
    font-size: 10.5px;
    font-weight: 700;
    padding: 5px 12px;
    border-radius: 6px;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.2s ease;
  }
  .mode-btn-crisis {
    background: rgba(239, 68, 68, 0.15);
    border-color: rgba(239, 68, 68, 0.5);
    color: #FF8080;
  }
  .mode-btn-crisis.active, .mode-btn-crisis:hover {
    background: #EF4444;
    color: #FFFFFF;
    box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
  }
  .mode-btn-solution {
    background: rgba(0, 210, 190, 0.15);
    border-color: rgba(0, 210, 190, 0.5);
    color: #00D2BE;
  }
  .mode-btn-solution.active, .mode-btn-solution:hover {
    background: #00D2BE;
    color: #05070A;
    box-shadow: 0 0 10px rgba(0, 210, 190, 0.5);
  }
  .speed-slider-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: monospace;
    font-size: 11px;
    color: #94A3B8;
  }
  .speed-slider-wrap input[type=range] {
    accent-color: #00D2BE;
    width: 95px;
    cursor: pointer;
  }

  /* Canvas Stage */
  .canvas-stage {
    position: relative;
    background: #040609;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    overflow: hidden;
    height: 250px;
  }
  #f1Canvas {
    width: 100%;
    height: 250px;
    display: block;
  }

  /* Telemetry Grid */
  .telem-strip {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 8px;
  }
  .telem-box {
    background: rgba(15, 20, 29, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    padding: 6px 8px;
    text-align: center;
  }
  .telem-lbl {
    font-size: 9px;
    color: #94A3B8;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.5px;
  }
  .telem-val {
    font-size: 16px;
    font-weight: 800;
    color: #FFFFFF;
    font-family: monospace;
    margin-top: 2px;
  }
  .telem-sub {
    font-size: 9.5px;
    font-family: monospace;
    margin-top: 1px;
  }

  /* Dynamic Alert Banner */
  .alert-banner {
    padding: 7px 12px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all 0.25s ease;
  }
  .alert-green {
    background: rgba(0, 210, 190, 0.12);
    border: 1px solid #00D2BE;
    color: #00D2BE;
  }
  .alert-red {
    background: rgba(239, 68, 68, 0.16);
    border: 1px solid #EF4444;
    color: #FFA3A3;
  }

  /* Problem vs Solution Deep Dive Cards */
  .solution-matrix {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
  .matrix-card {
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 11px;
    line-height: 1.4;
  }
  .matrix-crisis {
    background: rgba(239, 68, 68, 0.05);
    border: 1px solid rgba(239, 68, 68, 0.25);
    border-left: 4px solid #EF4444;
  }
  .matrix-solution {
    background: rgba(0, 210, 190, 0.05);
    border: 1px solid rgba(0, 210, 190, 0.25);
    border-left: 4px solid #00D2BE;
  }
  .matrix-head {
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 3px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .matrix-desc {
    color: #CBD5E1;
    font-size: 10.5px;
  }
</style>
</head>
<body>
<div class="hud-container">

  <!-- Top Control Bar -->
  <div class="control-bar">
    <div class="branding-tag">
      <span class="pulse-live"></span>
      <span>AEROCAP // MERCEDES-AMG PETRONAS GROUND-EFFECT CORRELATION SUITE</span>
    </div>
    <div class="controls-right">
      <button class="mode-btn mode-btn-crisis" id="btnCrisis">🔴 Simulate Mercedes Crisis (W13/W14 Stall)</button>
      <button class="mode-btn mode-btn-solution active" id="btnSolution">🛡️ AEROCAP Protected Interceptor</button>
      <button class="mode-btn" id="btnAudio" style="background:rgba(255,255,255,0.06); border-color:rgba(255,255,255,0.18); color:#94A3B8;">🔇 Pit Audio: OFF</button>
      <div class="speed-slider-wrap">
        <span>VELOCITY:</span>
        <input type="range" id="speedSlider" min="200" max="345" value="324">
        <span id="sliderDisp" style="color:#FFFFFF; font-weight:700;">324 km/h</span>
      </div>
    </div>
  </div>

  <!-- 60 FPS Physics & Flow Canvas -->
  <div class="canvas-stage">
    <canvas id="f1Canvas" width="960" height="250"></canvas>
  </div>

  <!-- Live Telemetry Strip -->
  <div class="telem-strip">
    <div class="telem-box">
      <div class="telem-lbl">Chassis Velocity</div>
      <div class="telem-val" id="valSpeed">324 km/h</div>
      <div class="telem-sub" style="color:#94A3B8;">Wellington Straight</div>
    </div>
    <div class="telem-box">
      <div class="telem-lbl">Dynamic Ride Height</div>
      <div class="telem-val" id="valHeight" style="color:#00D2BE;">13.2 mm</div>
      <div class="telem-sub" id="subHeight" style="color:#00D2BE;">Clearance OK</div>
    </div>
    <div class="telem-box">
      <div class="telem-lbl">Ground-Effect Downforce</div>
      <div class="telem-val" id="valDownforce">31.4 kN</div>
      <div class="telem-sub" id="subDownforce" style="color:#00D2BE;">Venturi Attached</div>
    </div>
    <div class="telem-box">
      <div class="telem-lbl">Vertical Vibration (Gz)</div>
      <div class="telem-val" id="valGz" style="color:#00D2BE;">±0.15 G</div>
      <div class="telem-sub" id="subGz" style="color:#94A3B8;">Stable Baseline</div>
    </div>
    <div class="telem-box">
      <div class="telem-lbl">Autoclave Spend Gate</div>
      <div class="telem-val" id="valSpend" style="color:#00D2BE;">£450,000</div>
      <div class="telem-sub" id="subSpend" style="color:#00D2BE;">CAPEX PROTECTED</div>
    </div>
  </div>

  <!-- Dynamic Alert Banner -->
  <div class="alert-banner alert-green" id="alertBanner">
    <span id="alertText">✅ <b>STABLE BOUNDARY LAYER:</b> Flow attached through Venturi tunnels (CCI = 0.94 >= 0.85). Stage Gate 3 Autoclave Manufacturing released.</span>
    <span id="alertSunk" style="font-family: monospace;">FUNDS AT RISK: £0.00</span>
  </div>

  <!-- Problem vs Solution Deep Dive Comparison -->
  <div class="solution-matrix">
    <div class="matrix-card matrix-crisis">
      <div class="matrix-head" style="color:#EF4444;">
        <span>🚨 THE MERCEDES GROUND-EFFECT CRISIS (What Broke W13 & W14)</span>
      </div>
      <div class="matrix-desc">
        <b>The Aero Trap:</b> CFD & 60% wind tunnels test at fixed 30mm ride heights without dynamic aero-elasticity. At 320+ km/h on track, suction sucks the flexible floor down to 11mm, choking Venturi flow into severe 6.2 Hz porpoising.<br>
        <b>The Cost Cap Penalty:</b> Committing unproven floors straight into autoclave tooling wastes <b>£450,000</b> in scrapped carbon molds + <b>£320,000</b> in TD017 redundant inventory write-offs under FIA Issue 24.
      </div>
    </div>

    <div class="matrix-card matrix-solution">
      <div class="matrix-head" style="color:#00D2BE;">
        <span>🛡️ THE AEROCAP UNIQUE SOLUTION (Why This Platform Wins)</span>
      </div>
      <div class="matrix-desc">
        <b>Closed-Loop Correlation Bridge:</b> Correlates 7-Post shaker dynamic modal response, optical laser ride-height sensors, and CFD mesh in a sub-second loop.<br>
        <b>Automated Stage Gate 3 Lock:</b> The instant Correlation Confidence (CCI) drops below 0.85, the engine locks autoclave tooling spend within 0.04s—protecting <b>£450,000</b> in certified cost-cap headroom and reallocating compute to anti-stall edge-vortices.
      </div>
    </div>
  </div>

</div>

<script>
  const canvas = document.getElementById('f1Canvas');
  const ctx = canvas.getContext('2d');

  let mode = 'solution'; // 'crisis' or 'solution'
  let targetSpeed = 324;
  let currentSpeed = 324;
  let frame = 0;
  let particles = [];
  let sparks = [];
  let gHistory = new Array(60).fill(0);

  // Web Audio Synthesizer State
  let audioEnabled = false;
  let audioCtx = null;
  let oscEngine = null;
  let oscTurbo = null;
  let gainNode = null;
  let hasTriggeredRadio = false;

  // Initialize airflow streamlines
  for (let i = 0; i < 110; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: 110 + Math.random() * 95,
      speed: 4 + Math.random() * 7,
      size: 1.2 + Math.random() * 2,
      opacity: 0.25 + Math.random() * 0.75
    });
  }

  // DOM Controls
  const btnCrisis = document.getElementById('btnCrisis');
  const btnSolution = document.getElementById('btnSolution');
  const btnAudio = document.getElementById('btnAudio');
  const speedSlider = document.getElementById('speedSlider');
  const sliderDisp = document.getElementById('sliderDisp');

  btnCrisis.addEventListener('click', () => {
    mode = 'crisis';
    btnCrisis.classList.add('active');
    btnSolution.classList.remove('active');
  });

  btnSolution.addEventListener('click', () => {
    mode = 'solution';
    btnSolution.classList.add('active');
    btnCrisis.classList.remove('active');
  });

  btnAudio.addEventListener('click', () => {
    audioEnabled = !audioEnabled;
    if (audioEnabled) {
      btnAudio.innerText = "🔊 Pit Audio: ON";
      btnAudio.style.color = "#00D2BE";
      btnAudio.style.borderColor = "#00D2BE";
      initAudio();
    } else {
      btnAudio.innerText = "🔇 Pit Audio: OFF";
      btnAudio.style.color = "#94A3B8";
      btnAudio.style.borderColor = "rgba(255,255,255,0.18)";
      if (gainNode && audioCtx) {
        gainNode.gain.setValueAtTime(0, audioCtx.currentTime);
      }
    }
  });

  function initAudio() {
    try {
      if (!audioCtx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        audioCtx = new AudioContext();

        oscEngine = audioCtx.createOscillator();
        oscEngine.type = 'sawtooth';

        oscTurbo = audioCtx.createOscillator();
        oscTurbo.type = 'sine';

        gainNode = audioCtx.createGain();
        gainNode.gain.setValueAtTime(0.025, audioCtx.currentTime);

        oscEngine.connect(gainNode);
        oscTurbo.connect(gainNode);
        gainNode.connect(audioCtx.destination);

        oscEngine.start();
        oscTurbo.start();
      }
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
      if (gainNode && audioCtx) {
        gainNode.gain.setValueAtTime(0.025, audioCtx.currentTime);
      }
    } catch(e) {}
  }

  speedSlider.addEventListener('input', (e) => {
    targetSpeed = parseInt(e.target.value);
    sliderDisp.innerText = `${targetSpeed} km/h`;
  });

  function animate() {
    frame++;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Smooth speed transition
    currentSpeed += (targetSpeed - currentSpeed) * 0.06;

    // Aero suction formula
    const compression = ((currentSpeed / 340) ** 2) * 19;
    let rideHeight = 31 - compression;

    // Check stall condition: ride height < 15.0 mm in Crisis Mode
    const isStalled = (mode === 'crisis' && rideHeight < 15.2);
    
    // Porpoising physics oscillation
    let bounceY = 0;
    let verticalG = 0.15;
    if (isStalled) {
      // 6.2 Hz violent porpoising
      bounceY = Math.sin(frame * 0.42) * 9.5;
      verticalG = Math.sin(frame * 0.42) * 3.4;

      // Bottoming out on asphalt generates sparks
      if (bounceY > 5.5) {
        for (let s = 0; s < 4; s++) {
          sparks.push({
            x: 440 + Math.random() * 40,
            y: 216 + Math.random() * 3,
            vx: -(currentSpeed / 20 + Math.random() * 6),
            vy: -(Math.random() * 3.5),
            life: 18 + Math.random() * 12
          });
        }
      }
    } else {
      verticalG = (Math.sin(frame * 0.08) * 0.18);
    }

    // Audio Engine Update (V6 Hybrid Synth & Radio Alert)
    if (audioEnabled && audioCtx && oscEngine && oscTurbo && gainNode) {
      const baseFreq = 85 + (currentSpeed / 345) * 240;
      oscEngine.frequency.setTargetAtTime(baseFreq, audioCtx.currentTime, 0.05);

      const turboFreq = 1500 + (currentSpeed / 345) * 1500;
      oscTurbo.frequency.setTargetAtTime(turboFreq, audioCtx.currentTime, 0.05);

      if (isStalled) {
        gainNode.gain.setTargetAtTime(0.045 + Math.sin(frame * 0.42) * 0.015, audioCtx.currentTime, 0.02);
        if (!hasTriggeredRadio) {
          hasTriggeredRadio = true;
          try {
            if ('speechSynthesis' in window) {
              const radioSpeech = new SpeechSynthesisUtterance("Correlation alarm. Boundary detachment. Stage Gate 3 locked.");
              radioSpeech.rate = 1.05;
              radioSpeech.pitch = 0.95;
              window.speechSynthesis.speak(radioSpeech);
            }
          } catch(e) {}
        }
      } else {
        gainNode.gain.setTargetAtTime(0.025, audioCtx.currentTime, 0.05);
        hasTriggeredRadio = false;
      }
    }

    // Push vertical G to history for mini-oscilloscope
    gHistory.push(verticalG);
    if (gHistory.length > 60) gHistory.shift();

    // 1. Draw Asphalt Track
    ctx.fillStyle = '#070A0F';
    ctx.fillRect(0, 215, canvas.width, 35);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(0, 215);
    ctx.lineTo(canvas.width, 215);
    ctx.stroke();

    // Track Curb (Alternating Mercedes Teal / White)
    const curbStep = 24;
    const curbOffset = (frame * (currentSpeed / 14)) % (curbStep * 2);
    for (let cx = -curbStep * 2; cx < canvas.width + curbStep * 2; cx += curbStep) {
      const isTeal = Math.floor((cx + curbOffset) / curbStep) % 2 === 0;
      ctx.fillStyle = isTeal ? '#00D2BE' : '#FFFFFF';
      ctx.fillRect(cx - curbOffset, 215, curbStep, 4);
    }

    // Dashed moving center line
    const dashOffset = (frame * (currentSpeed / 12)) % 60;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.18)';
    ctx.lineWidth = 2;
    ctx.setLineDash([30, 30]);
    ctx.lineDashOffset = -dashOffset;
    ctx.beginPath();
    ctx.moveTo(0, 232);
    ctx.lineTo(canvas.width, 232);
    ctx.stroke();
    ctx.setLineDash([]);

    // 2. Streamline Flow Particles
    particles.forEach(p => {
      p.x -= (currentSpeed / 24) + p.speed;
      if (p.x < 0) {
        p.x = canvas.width;
        p.y = 120 + Math.random() * 85;
      }

      // Deflection around underfloor Venturi
      let py = p.y;
      if (p.x > 260 && p.x < 720) {
        const tunnelArc = Math.sin((p.x - 260) / 460 * Math.PI);
        py += tunnelArc * 16;
        if (isStalled) {
          // Turbulent vortex eddies in stall
          py += Math.sin(frame * 0.45 + p.x * 0.08) * 8.5;
        }
      }

      ctx.fillStyle = isStalled 
        ? `rgba(239, 68, 68, ${p.opacity})` 
        : `rgba(0, 210, 190, ${p.opacity * 0.85})`;
      ctx.beginPath();
      ctx.arc(p.x, py, p.size, 0, Math.PI * 2);
      ctx.fill();
    });

    // 3. Render Sparks
    for (let s = sparks.length - 1; s >= 0; s--) {
      const sp = sparks[s];
      sp.x += sp.vx;
      sp.y += sp.vy;
      sp.vy += 0.22; // gravity
      sp.life--;
      if (sp.life <= 0 || sp.x < 0) {
        sparks.splice(s, 1);
        continue;
      }
      ctx.fillStyle = `rgba(255, ${Math.floor(160 + Math.random() * 80)}, 30, ${sp.life / 30})`;
      ctx.beginPath();
      ctx.arc(sp.x, sp.y, 1.8, 0, Math.PI * 2);
      ctx.fill();
    }

    // 4. Render High-Detail Mercedes W16 Vector Profile
    const carX = 260;
    const carY = 180 - (30 - rideHeight) * 1.5 + bounceY;

    ctx.save();
    ctx.translate(carX, carY);

    // Dynamic Floor Venturi Glowing Pressure Gradient (Attached vs Stalled)
    const floorGrad = ctx.createLinearGradient(40, 22, 380, 22);
    if (isStalled) {
      floorGrad.addColorStop(0, 'rgba(239, 68, 68, 0.4)');
      floorGrad.addColorStop(0.5, 'rgba(239, 68, 68, 0.8)');
      floorGrad.addColorStop(1, 'rgba(239, 68, 68, 0.3)');
    } else {
      floorGrad.addColorStop(0, 'rgba(0, 210, 190, 0.2)');
      floorGrad.addColorStop(0.4, 'rgba(0, 210, 190, 0.7)'); // Throat suction
      floorGrad.addColorStop(1, 'rgba(0, 210, 190, 0.3)');
    }
    ctx.fillStyle = floorGrad;
    ctx.fillRect(50, 18, 330, 8);

    // Main Carbon Monocoque & Bodywork
    ctx.beginPath();
    ctx.moveTo(430, 20); // Front nose tip
    ctx.lineTo(340, 8);  // Nosecone slope
    ctx.lineTo(260, -8); // Cockpit rim
    ctx.lineTo(210, -28);// Roll hoop / airbox
    ctx.lineTo(170, -28);
    ctx.lineTo(130, -12);// Shark fin spine
    ctx.lineTo(40, -6);  // Engine cowl
    ctx.lineTo(0, 18);   // Rear diffuser exit
    ctx.lineTo(70, 20);  // Underfloor plank
    ctx.lineTo(390, 20);
    ctx.closePath();
    ctx.fillStyle = '#0F131A';
    ctx.fill();
    ctx.strokeStyle = isStalled ? '#EF4444' : '#00D2BE';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Mercedes Star & Silver Gradient on Engine Cover
    const liveryGrad = ctx.createLinearGradient(130, -25, 230, 5);
    liveryGrad.addColorStop(0, 'rgba(255, 255, 255, 0.35)');
    liveryGrad.addColorStop(0.5, 'rgba(0, 210, 190, 0.4)');
    liveryGrad.addColorStop(1, 'transparent');
    ctx.fillStyle = liveryGrad;
    ctx.beginPath();
    ctx.moveTo(210, -26);
    ctx.lineTo(170, -26);
    ctx.lineTo(120, -10);
    ctx.lineTo(160, 5);
    ctx.closePath();
    ctx.fill();

    // Halo Safety Structure & Driver Helmet
    // Helmet
    ctx.fillStyle = '#E2E8F0';
    ctx.beginPath();
    ctx.arc(235, -12, 8, 0, Math.PI * 2);
    ctx.fill();
    // Visor
    ctx.fillStyle = '#00D2BE';
    ctx.fillRect(238, -14, 5, 4);
    // Halo titanium loop
    ctx.strokeStyle = '#64748B';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(242, -10, 13, Math.PI * 0.9, Math.PI * 0.1, false);
    ctx.stroke();

    // Front Wing (4 Cascades + Endplate)
    ctx.fillStyle = '#00D2BE';
    ctx.fillRect(430, 18, 55, 5); // Mainplane
    ctx.fillStyle = '#1E293B';
    ctx.fillRect(440, 11, 42, 4); // Flap 1
    ctx.fillRect(448, 6, 32, 3);  // Flap 2
    ctx.fillStyle = '#00D2BE';
    ctx.fillRect(482, 4, 4, 19);  // Endplate diveplane

    // Rear Wing (Dual Element + DRS Pylon)
    ctx.fillStyle = '#00D2BE';
    ctx.fillRect(-15, -34, 38, 7); // Main beam
    ctx.fillStyle = '#334155';
    ctx.fillRect(-12, -42, 34, 5); // Upper DRS flap
    ctx.fillRect(10, -26, 5, 44);  // Swan-neck pylon
    ctx.fillRect(-16, -44, 4, 36); // Endplate

    // Wheels (Pirelli 18-Inch Soft Tires)
    [50, 380].forEach(wx => {
      // Tire Rubber
      ctx.fillStyle = '#000000';
      ctx.strokeStyle = '#EF4444'; // Red soft stripe
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(wx, 16, 21, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      // Carbon Aero Wheel Cover
      ctx.fillStyle = '#111827';
      ctx.beginPath();
      ctx.arc(wx, 16, 14, 0, Math.PI * 2);
      ctx.fill();

      // Spinning Rim Spokes
      const spinAngle = frame * (currentSpeed / 10);
      ctx.save();
      ctx.translate(wx, 16);
      ctx.rotate(spinAngle);
      ctx.strokeStyle = '#00D2BE';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(-12, 0); ctx.lineTo(12, 0);
      ctx.moveTo(0, -12); ctx.lineTo(0, 12);
      ctx.stroke();
      ctx.restore();
    });

    ctx.restore();

    // 5. Inset Real-Time G-Force Oscilloscope (Top Right of Canvas)
    const oscX = 760;
    const oscY = 12;
    const oscW = 185;
    const oscH = 68;

    ctx.fillStyle = 'rgba(10, 15, 24, 0.88)';
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(oscX, oscY, oscW, oscH, 6);
    ctx.fill();
    ctx.stroke();

    // Scope Header
    ctx.fillStyle = '#94A3B8';
    ctx.font = '700 9px monospace';
    ctx.fillText('VERTICAL ACCEL (Gz) // 60 FPS', oscX + 8, oscY + 14);

    // Center Baseline
    const midY = oscY + 40;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.beginPath();
    ctx.moveTo(oscX + 6, midY);
    ctx.lineTo(oscX + oscW - 6, midY);
    ctx.stroke();

    // Waveform Trace
    ctx.strokeStyle = isStalled ? '#EF4444' : '#00D2BE';
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < gHistory.length; i++) {
      const gx = oscX + 8 + (i / 60) * (oscW - 16);
      const gy = midY - (gHistory[i] * 6.5);
      if (i === 0) ctx.moveTo(gx, gy);
      else ctx.lineTo(gx, gy);
    }
    ctx.stroke();

    // Scope Value Text
    ctx.fillStyle = isStalled ? '#EF4444' : '#00D2BE';
    ctx.font = '800 11px monospace';
    ctx.textAlign = 'right';
    ctx.fillText(`${verticalG > 0 ? '+' : ''}${verticalG.toFixed(2)} G`, oscX + oscW - 8, oscY + 14);
    ctx.textAlign = 'left';

    // 6. Floating Canvas Annotation Callout
    if (isStalled) {
      ctx.fillStyle = 'rgba(239, 68, 68, 0.9)';
      ctx.beginPath();
      ctx.roundRect(290, 85, 380, 24, 4);
      ctx.fill();
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '700 10.5px monospace';
      ctx.fillText('🚨 VENTURI STALL: BOUNDARY SEPARATION | 6.2 Hz PORPOISING', 300, 101);
    } else {
      ctx.fillStyle = 'rgba(0, 210, 190, 0.18)';
      ctx.strokeStyle = '#00D2BE';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(290, 85, 380, 24, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = '#00D2BE';
      ctx.font = '700 10.5px monospace';
      ctx.fillText('✅ ATTACHED VENTURI FLOW: Cp = -2.85 | DOWNFORCE ATTACHED', 300, 101);
    }

    // 7. Update Live Telemetry Metrics
    document.getElementById('valSpeed').innerText = `${Math.round(currentSpeed)} km/h`;
    document.getElementById('valHeight').innerText = `${rideHeight.toFixed(1)} mm`;
    
    const subHeight = document.getElementById('subHeight');
    if (rideHeight < 15.2) {
      subHeight.innerText = 'CRITICAL STALL ZONE';
      subHeight.style.color = '#EF4444';
      document.getElementById('valHeight').style.color = '#EF4444';
    } else {
      subHeight.innerText = 'Clearance Nominal';
      subHeight.style.color = '#00D2BE';
      document.getElementById('valHeight').style.color = '#00D2BE';
    }

    const maxDf = (0.5 * 1.225 * 3.8 * 1.6 * ((currentSpeed / 3.6) ** 2)) / 1000;
    const actualDf = isStalled ? (maxDf * 0.58) : maxDf;
    document.getElementById('valDownforce').innerText = `${actualDf.toFixed(1)} kN`;
    
    const subDownforce = document.getElementById('subDownforce');
    if (isStalled) {
      subDownforce.innerText = '-42% STALL COLLAPSE';
      subDownforce.style.color = '#EF4444';
      document.getElementById('valDownforce').style.color = '#EF4444';
    } else {
      subDownforce.innerText = 'Venturi Attached';
      subDownforce.style.color = '#00D2BE';
      document.getElementById('valDownforce').style.color = '#00D2BE';
    }

    document.getElementById('valGz').innerText = `${verticalG > 0 ? '+' : ''}${verticalG.toFixed(2)} G`;
    document.getElementById('valGz').style.color = isStalled ? '#EF4444' : '#00D2BE';
    document.getElementById('subGz').innerText = isStalled ? '6.2 Hz Porpoising' : 'Stable Dynamic Line';
    document.getElementById('subGz').style.color = isStalled ? '#EF4444' : '#94A3B8';

    // Spend & Banner Logic
    const alertBanner = document.getElementById('alertBanner');
    const alertText = document.getElementById('alertText');
    const alertSunk = document.getElementById('alertSunk');
    const valSpend = document.getElementById('valSpend');
    const subSpend = document.getElementById('subSpend');

    if (isStalled) {
      alertBanner.className = 'alert-banner alert-red';
      alertText.innerHTML = `🚨 <b>CORRELATION FAILURE DETECTED:</b> Boundary layer detachment at ${Math.round(currentSpeed)} km/h! <b>STAGE GATE 3 AUTOCLAVE TOOLING LOCKED.</b>`;
      alertSunk.innerHTML = '🛡️ SUNK SCRAP COST PREVENTED: £450,000.00';
      valSpend.innerText = '£450,000';
      valSpend.style.color = '#EF4444';
      subSpend.innerText = 'LOCKED // SHIELDED';
      subSpend.style.color = '#EF4444';
    } else {
      alertBanner.className = 'alert-banner alert-green';
      alertText.innerHTML = '✅ <b>STABLE ATTACHED FLOW:</b> Aerodynamic correlation verified (CCI >= 0.85). Stage Gate 3 Autoclave spend authorized.';
      alertSunk.innerHTML = 'FUNDS AT RISK: £0.00';
      valSpend.innerText = '£0.00';
      valSpend.style.color = '#00D2BE';
      subSpend.innerText = 'ZERO CAPITAL AT RISK';
      subSpend.style.color = '#00D2BE';
    }

    requestAnimationFrame(animate);
  }

  animate();
</script>
</body>
</html>
"""

components.html(live_presentation_html, height=680, scrolling=False)
st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)


# ==============================================================================
# MAIN TABS (CLEAN, HUMAN, PROFESSIONAL MOTORSPORT HEADERS)
# ==============================================================================
tab_corr, tab_telemetry, tab_pareto, tab_anomaly, tab_ops, tab_rollback, tab_monte, tab_fin = st.tabs([
    "Aerodynamic Correlation & 3D",
    "Silverstone Lap Telemetry",
    "Upgrade Strategy & Pareto",
    "Predictive Rig Health",
    "Facility Scheduling & OEE",
    "Emergency Rollback Engine",
    "Season Risk Forecast",
    "FIA Statutory Compliance"
])


# ------------------------------------------------------------------------------
# TAB 1: 3D AERODYNAMICS & STAGE GATE (MERCEDES CORE PROBLEM)
# ------------------------------------------------------------------------------
with tab_corr:
    st.markdown("### Aerodynamic Correlation Confidence & 3D Spatial Diagnostics")
    st.markdown(
        "<p style='color:#94A3B8; font-size:12px; margin-top:-6px;'>"
        "Addresses wind tunnel and CFD correlation disconnects before authorizing composite autoclave manufacturing capital."
        "</p>",
        unsafe_allow_html=True
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        # Telemetry Downforce Curve
        sample_ride_heights = np.linspace(12.0, 45.0, 30)
        wt_predicted = 18.0 - 0.15 * sample_ride_heights + 0.001 * (sample_ride_heights ** 2)
        track_actual = wt_predicted.copy()
        track_actual[sample_ride_heights < 22.0] *= (sample_ride_heights[sample_ride_heights < 22.0] / 22.0) ** 1.8

        fig_corr = go.Figure()
        fig_corr.add_trace(go.Scatter(
            x=sample_ride_heights, y=wt_predicted, mode="lines",
            name="Wind Tunnel Expected (App. 2)", line=dict(color="#64748B", width=2.5, dash="dash")
        ))
        fig_corr.add_trace(go.Scatter(
            x=sample_ride_heights, y=track_actual, mode="lines+markers",
            name="Track Optical Telemetry", line=dict(color="#00D2BE", width=2.5)
        ))
        fig_corr.update_layout(
            title="Aerodynamic Downforce (kN) vs Dynamic Ride Height (mm)",
            xaxis_title="Rear Ride Height (mm)", yaxis_title="Downforce (kN)",
            template="plotly_dark", height=320,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,21,28,0.6)",
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_corr, use_container_width=True)

    with c2:
        st.markdown("**Component Authorization Gate**")
        selected_comp = st.selectbox("Select Candidate Package", df_correlation["component_name"].tolist())
        comp_row = df_correlation[df_correlation["component_name"] == selected_comp].iloc[0]

        cci = comp_row["cci_score"]
        status = comp_row["stage_gate_status"]
        badge_style = "status-badge-approved" if status == "Approved" else "status-badge-locked"

        st.markdown(f"**Correlation Confidence Index (CCI):** `{cci:.2f}` / 1.00")
        st.progress(float(cci))
        st.markdown(f"**Stage Gate 3 Status:** <span class='status-badge {badge_style}'>{status.upper()}</span>", unsafe_allow_html=True)

        gate_eval = stage_manager.evaluate_gate_release(
            component_code=selected_comp,
            cci_score=cci,
            planned_tooling_cost_gbp=380_000.0,
            planned_autoclave_hours=44.0
        )
        st.info(gate_eval["gatekeeper_message"])
        if gate_eval["funds_protected_gbp"] > 0:
            st.success(f"🛡️ **Capital Protected:** £{gate_eval['funds_protected_gbp']:,.2f} in unrecoverable scrap avoided!")

    st.markdown("---")
    st.markdown("### Multi-Perspective 3D Diagnostic Suite")
    
    # 3D Layout 1: Underfloor Venturi Pressure Map
    st.markdown("**3D Layout 1 // Underfloor Venturi Ground-Effect Pressure Coefficient ($C_p$)**")
    simulated_ride_height = st.slider("Chassis Operating Ride Height (mm)", min_value=10.0, max_value=35.0, value=19.0, step=1.0)
    
    x_grid = np.linspace(-1.5, 1.5, 30)
    y_grid = np.linspace(0, 3.5, 30)
    X, Y = np.meshgrid(x_grid, y_grid)
    throat_suction = -3.2 * (25.0 / max(simulated_ride_height, 12.0))
    stall_penalty = 1.6 if simulated_ride_height < 16.0 else 0.0
    Z_pressure = throat_suction * np.exp(-((Y - 1.8)**2)/0.6) * (1 - 0.4*(X**2)) + stall_penalty

    fig_3d = go.Figure(data=[go.Surface(
        z=Z_pressure, x=X, y=Y,
        colorscale="Viridis",
        colorbar=dict(title="Cp")
    )])
    status_label = "⚠️ SEVERE BOUNDARY LAYER DETACHMENT (PORPOISING ONSET)" if simulated_ride_height < 16.0 else "✅ STABLE ATTACHED GROUND-EFFECT FLOW"
    fig_3d.update_layout(
        title=f"Underfloor Pressure Profile ({simulated_ride_height}mm) — {status_label}",
        scene=dict(
            xaxis_title="Floor Span (m)",
            yaxis_title="Length (m)",
            zaxis_title="Pressure (Cp)"
        ),
        template="plotly_dark", height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_3d, use_container_width=True)

    # 3D Layout 2 & 3
    col_3d_1, col_3d_2 = st.columns(2)
    with col_3d_1:
        st.markdown("**3D Layout 2 // 7-Post Shaker Dynamic Chassis Heave & Roll Mesh**")
        chassis_x = np.array([-0.9, 0.9, 1.0, -1.0, -0.9, 0.0, 0.9, 0.0, -1.0, 1.0])
        chassis_y = np.array([-1.8, -1.8, 1.8, 1.8, -1.8, -0.4, -1.8, -0.4, 1.8, 1.8])
        chassis_z = np.array([0.2, 0.2, 0.25, 0.25, 0.2, 0.95, 0.2, 0.95, 0.25, 0.25])
        heave_val = 0.05 * np.sin(simulated_ride_height)

        fig_shaker3d = go.Figure(data=[
            go.Scatter3d(
                x=chassis_x, y=chassis_y, z=chassis_z + heave_val,
                mode="lines+markers",
                line=dict(color="#00D2BE", width=5),
                marker=dict(size=4, color="#FFFFFF"),
                name="W16 Spatial Frame"
            )
        ])
        fig_shaker3d.update_layout(
            scene=dict(xaxis_title="Width", yaxis_title="Length", zaxis_title="Heave"),
            title="Rigid Chassis Heave & Torsional Deflection",
            template="plotly_dark", height=360,
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig_shaker3d, use_container_width=True)

    with col_3d_2:
        st.markdown("**3D Layout 3 // Wind Tunnel 60% Scale Aerodynamic Flow Cones**")
        u_pts = np.linspace(-1.2, 1.2, 6)
        v_pts = np.linspace(-1.8, 1.8, 7)
        w_pts = np.linspace(0.1, 0.9, 4)
        U_grid, V_grid, W_grid = np.meshgrid(u_pts, v_pts, w_pts)
        vel_x = 0.15 * U_grid
        vel_y = np.ones_like(V_grid) * 77.0 * (1 - 0.25 * np.exp(-(U_grid**2 + W_grid**2)))
        vel_z = -0.1 * W_grid

        fig_flow3d = go.Figure(data=[
            go.Cone(
                x=U_grid.flatten(), y=V_grid.flatten(), z=W_grid.flatten(),
                u=vel_x.flatten(), v=vel_y.flatten(), w=vel_z.flatten(),
                colorscale="Tealgrn",
                sizemode="scaled", sizeref=2.5,
                colorbar=dict(title="Velocity (m/s)")
            )
        ])
        fig_flow3d.update_layout(
            scene=dict(xaxis_title="Span", yaxis_title="Streamwise", zaxis_title="Vertical"),
            title="Tunnel Streamwise Velocity Vector Field (77 m/s)",
            template="plotly_dark", height=360,
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig_flow3d, use_container_width=True)


# ------------------------------------------------------------------------------
# TAB 2: SILVERSTONE TRACK TELEMETRY
# ------------------------------------------------------------------------------
with tab_telemetry:
    st.markdown("### On-Track Telemetry Analysis // Silverstone Grand Prix")
    st.markdown(
        "<p style='color:#94A3B8; font-size:12px; margin-top:-6px;'>"
        "High-frequency car telemetry (Speed, Throttle, Aerodynamic Downforce, Heave Compression, and Russell vs. Verstappen Delta)."
        "</p>",
        unsafe_allow_html=True
    )

    telem_view = st.radio(
        "Telemetry Inspection Mode",
        ["Head-to-Head: Russell (W15) vs. Verstappen (RB20)", "Russell Single-Lap Baseline"],
        horizontal=True
    )

    if telem_view == "Head-to-Head: Russell (W15) vs. Verstappen (RB20)":
        comp_res = telemetry_analyzer.load_comparative_telemetry(driver_a="RUS", driver_b="VER")
        df_comp = comp_res["comparison_df"]

        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        with col_c1:
            st.metric("Maggotts-Becketts Deficit", f"+{comp_res['total_lost_in_mb_ms']:.1f} ms", "Time Lost in S-Curves")
        with col_c2:
            st.metric("Floor Ride Height Gap", f"+{comp_res['avg_rh_gap_mb_mm']:.1f} mm", "Mercedes Forced Higher")
        with col_c3:
            st.metric("Becketts Apex Speed Delta", "-7.5 km/h", "Downforce Limited")
        with col_c4:
            st.metric("Total Lap Delta", f"+{comp_res['final_lap_delta_sec']:.3f} s", "Qualifying Pace Gap")

        col_p1, col_p2 = st.columns([2, 1])
        with col_p1:
            # Comparative Speed Overlay
            fig_comp_speed = go.Figure()
            fig_comp_speed.add_trace(go.Scatter(
                x=df_comp["distance_m"], y=df_comp["speed_rus"],
                mode="lines", name="George Russell (W15)", line=dict(color="#00D2BE", width=2.2)
            ))
            fig_comp_speed.add_trace(go.Scatter(
                x=df_comp["distance_m"], y=df_comp["speed_ver"],
                mode="lines", name="Max Verstappen (RB20)", line=dict(color="#3B82F6", width=2.0, dash="dash")
            ))
            fig_comp_speed.add_vrect(x0=3100, x1=3500, fillcolor="rgba(245, 158, 11, 0.12)", line_width=0, annotation_text="Copse (Turn 9)")
            fig_comp_speed.add_vrect(x0=3600, x1=4500, fillcolor="rgba(239, 68, 68, 0.15)", line_width=0, annotation_text="Maggotts-Becketts (+82ms Deficit)")
            fig_comp_speed.update_layout(
                title="Telemetry Overlay: Speed Trace (km/h) along Silverstone Track (5,891m)",
                xaxis_title="Distance (m)", yaxis_title="Speed (km/h)",
                template="plotly_dark", height=320,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,21,28,0.6)",
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_comp_speed, use_container_width=True)

            # Dynamic Floor Clearance & Aerodynamic Compromise
            fig_comp_rh = go.Figure()
            fig_comp_rh.add_trace(go.Scatter(
                x=df_comp["distance_m"], y=df_comp["ride_height_rus"],
                mode="lines", name="Russell Dynamic Height (W15)", line=dict(color="#00D2BE", width=2.2)
            ))
            fig_comp_rh.add_trace(go.Scatter(
                x=df_comp["distance_m"], y=df_comp["ride_height_ver"],
                mode="lines", name="Verstappen Dynamic Height (RB20)", line=dict(color="#3B82F6", width=2.0, dash="dash")
            ))
            fig_comp_rh.add_hline(y=11.0, line_dash="dot", line_color="#EF4444", annotation_text="Plank Wear / Stall Boundary (11.0mm)")
            fig_comp_rh.add_vrect(x0=3600, x1=4500, fillcolor="rgba(239, 68, 68, 0.12)", line_width=0)
            fig_comp_rh.update_layout(
                title="Dynamic Floor Height (mm): Mercedes Setup Compromise vs Red Bull Stable Ground Effect",
                xaxis_title="Distance (m)", yaxis_title="Ride Height (mm)",
                template="plotly_dark", height=280,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,21,28,0.6)",
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_comp_rh, use_container_width=True)

        with col_p2:
            st.markdown("#### The Correlation Disconnect Diagnosed")
            st.markdown(
                """
                **1. Maggotts-Becketts High-G Inversion:**  
                Through the rapid directional changes (Turns 10-14, 260 km/h), the RB20 maintains a dynamic floor clearance of **10.2mm**, generating attached suction.  
                
                **2. Mercedes Forced Ride-Height Penalty:**  
                Because CFD did not accurately model floor edge flexibility under dynamic lateral roll, the W15 suffered boundary layer detachment when running below 14mm. Mercedes had to artificially raise the car by **+3.8mm**, sacrificing 2.8 kN of downforce and bleeding **82 milliseconds** in a single complex.
                
                **3. How AEROCAP Resolves This:**  
                The 7-Post Shaker & Correlation Engine directly computes the aero-elastic roll stiffness threshold, locking autoclave tooling before non-conforming floors are manufactured.
                """
            )

    else:
        df_tel = telemetry_analyzer.load_telemetry_lap(use_live_api=False)

        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            fig_speed = go.Figure()
            fig_speed.add_trace(go.Scatter(
                x=df_tel["distance_m"], y=df_tel["speed_kmh"],
                mode="lines", name="Speed (km/h)", line=dict(color="#00D2BE", width=2)
            ))
            fig_speed.add_trace(go.Scatter(
                x=df_tel["distance_m"], y=df_tel["aerodynamic_downforce_kn"] * 10.0,
                mode="lines", name="Downforce (kN x10)", line=dict(color="#F59E0B", width=1.8, dash="dot")
            ))
            fig_speed.update_layout(
                title="Track Distance (5,891m) vs Velocity & Aerodynamic Load",
                xaxis_title="Distance (m)", yaxis_title="Speed / Downforce",
                template="plotly_dark", height=360,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,21,28,0.6)",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_speed, use_container_width=True)

        with col_t2:
            st.markdown("**Corner Telemetry Insights**")
            st.metric("Top Speed (Hangar)", f"{df_tel['speed_kmh'].max():.1f} km/h")
            st.metric("Peak Aero Load", f"{df_tel['aerodynamic_downforce_kn'].max():.1f} kN")
            st.metric("Minimum Ride Height", f"{df_tel['front_ride_height_mm'].min():.1f} mm")
            st.caption("High downforce compresses front springs, driving chassis into the sensitive correlation boundary.")


# ------------------------------------------------------------------------------
# TAB 3: PARETO UPGRADE OPTIMIZATION
# ------------------------------------------------------------------------------
with tab_pareto:
    st.markdown("### Multi-Objective Pareto Frontier Upgrade Strategy")
    st.markdown(
        "<p style='color:#94A3B8; font-size:12px; margin-top:-6px;'>"
        "Identifies mathematically non-dominated aero packages balancing Downforce Points vs Cost (£) vs Autoclave Hours."
        "</p>",
        unsafe_allow_html=True
    )

    col_p1, col_p2 = st.columns([1, 2])
    with col_p1:
        st.markdown("**Operational Budget Limits**")
        budget_limit = st.slider("Package Cost Cap (£)", min_value=100_000, max_value=500_000, value=400_000, step=25_000)
        autoclave_limit = st.slider("Autoclave Shop Hours", min_value=10, max_value=60, value=50, step=5)
        
        opt = ParetoUpgradeOptimizer(max_budget_gbp=budget_limit, max_autoclave_hours=autoclave_limit)
        df_pareto_res = opt.identify_pareto_frontier(df_upgrades)
        ranked_upgrades = opt.rank_optimal_packages(df_pareto_res)

        st.markdown("**Cost-per-Millisecond Leaderboard**")
        st.dataframe(
            ranked_upgrades[["upgrade_code", "cost_per_ms_gbp", "lap_time_delta_sec", "is_pareto_optimal"]].rename(
                columns={"cost_per_ms_gbp": "Cost/ms (£)", "lap_time_delta_sec": "Lap Delta (s)", "is_pareto_optimal": "Pareto"}
            ),
            hide_index=True,
            use_container_width=True
        )

    with col_p2:
        fig_pareto = px.scatter(
            df_pareto_res,
            x="manufacturing_cost_gbp",
            y="projected_downforce_gain",
            size="autoclave_hours",
            color="is_pareto_optimal",
            hover_name="upgrade_code",
            hover_data=["lap_time_delta_sec", "cost_per_ms_gbp", "lead_time_days"],
            color_discrete_map={True: "#00D2BE", False: "#EF4444"},
            labels={
                "manufacturing_cost_gbp": "Cost (£)",
                "projected_downforce_gain": "Downforce Gain (pts)",
                "is_pareto_optimal": "Pareto Frontier"
            },
            title="Pareto Optimal Frontier: Downforce vs Cost Cap Expenditure (£)"
        )
        fig_pareto.update_layout(
            template="plotly_dark", height=410,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,21,28,0.6)",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_pareto, use_container_width=True)


# ------------------------------------------------------------------------------
# TAB 4: PREDICTIVE RIG HEALTH (ML)
# ------------------------------------------------------------------------------
with tab_anomaly:
    st.markdown("### Unsupervised Machine Learning Telemetry Watchdog")
    st.markdown(
        "<p style='color:#94A3B8; font-size:12px; margin-top:-6px;'>"
        "Isolation Forest algorithm predicting mechanical failure on DYN-01 Powertrain Bench and RIG-02 Shaker."
        "</p>",
        unsafe_allow_html=True
    )

    detector = RigTelemetryAnomalyDetector(contamination=0.04)
    np.random.seed(42)
    n_pts = 100
    times = [datetime.now(timezone.utc) - pd.Timedelta(seconds=5 * (n_pts - i)) for i in range(n_pts)]
    vibrations = np.random.normal(0.42, 0.04, n_pts)
    temps = np.random.normal(68.0, 1.5, n_pts)
    pressures = np.random.normal(4.8, 0.1, n_pts)
    torques = np.random.normal(320.0, 8.0, n_pts)

    vibrations[85:90] = np.linspace(1.8, 4.2, 5)
    temps[85:90] = np.linspace(88.0, 118.0, 5)
    pressures[85:90] = np.linspace(3.1, 1.7, 5)

    df_stream = pd.DataFrame({
        "timestamp": times,
        "vibration_rms_g": vibrations,
        "bearing_temp_c": temps,
        "oil_pressure_bar": pressures,
        "shaft_torque_nm": torques
    })

    analyzed = detector.predict_anomalies(df_stream)
    report = detector.generate_incident_report(analyzed, facility_id="DYN-01")

    ac1, ac2 = st.columns([3, 1])
    with ac1:
        fig_telemetry = go.Figure()
        fig_telemetry.add_trace(go.Scatter(
            x=analyzed["timestamp"], y=analyzed["vibration_rms_g"],
            mode="lines", name="Vibration RMS (g)", line=dict(color="#94A3B8")
        ))
        anom_pts = analyzed[analyzed["is_anomaly"]]
        fig_telemetry.add_trace(go.Scatter(
            x=anom_pts["timestamp"], y=anom_pts["vibration_rms_g"],
            mode="markers", name="Anomalous Spike", marker=dict(color="#EF4444", size=9, symbol="x")
        ))
        fig_telemetry.update_layout(
            title="DYN-01 Real-Time Bearing Vibration Telemetry",
            xaxis_title="Time", yaxis_title="Vibration (g)",
            template="plotly_dark", height=340,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,21,28,0.6)",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_telemetry, use_container_width=True)

    with ac2:
        st.markdown("**Predictive Diagnostic State**")
        if report["status"] == "CRITICAL_ANOMALY_DETECTED":
            st.error("🚨 ANOMALY CONFIRMED")
            st.markdown(f"Peak Vibration: **{report['triggering_vibration_g']:.2f}g**")
            st.markdown(f"Bearing Temp: **{report['triggering_temp_c']:.1f}°C**")
            st.markdown(f"Damage Avoided: **£{report['estimated_damage_avoided_gbp']:,.0f}**")
            st.warning(report["recommended_action"])
        else:
            st.success("✅ Powertrain Bench Healthy")


# ------------------------------------------------------------------------------
# TAB 5: CRITICAL PATH FACILITY OEE
# ------------------------------------------------------------------------------
with tab_ops:
    st.markdown("### Critical Path Facility Operations & Rig Allocation")
    st.markdown(
        "<p style='color:#94A3B8; font-size:12px; margin-top:-6px;'>"
        "Coordinates manufacturing lead times with dyno test cell allocations to maximize OEE."
        "</p>",
        unsafe_allow_html=True
    )

    sched_res = scheduler.evaluate_schedule_feasibility(df_tests, df_parts)
    
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        st.markdown("**Test Cell Schedule Matrix**")
        st.dataframe(
            sched_res["detailed_schedule"][[
                "test_reference", "facility_id", "programme_type", "scheduled_start", 
                "part_number", "slip_days", "potential_idle_cost_gbp", "actual_status"
            ]].rename(columns={
                "test_reference": "Session", "facility_id": "Cell", "programme_type": "Programme",
                "part_number": "Critical Part", "slip_days": "Slip (Days)", "potential_idle_cost_gbp": "Idle Loss (£)",
                "actual_status": "Status"
            }),
            hide_index=True,
            use_container_width=True
        )

    with col_s2:
        st.markdown("**In-Process Revision Simulator**")
        part_select = st.selectbox("Select Component in Manufacture", df_parts["part_number"].head(8).tolist())
        target_part = df_parts[df_parts["part_number"] == part_select].iloc[0]
        wip_pct = st.slider("WIP Completion % when ECO Issued", 0.1, 0.9, 0.5)
        
        eco_result = scheduler.process_engineering_change_order(
            part_number=part_select,
            old_rev=target_part["revision"],
            new_rev="Rev C",
            wip_completion_pct=wip_pct,
            unit_cost_gbp=target_part["unit_cost_gbp"],
            added_lead_time_days=5
        )
        st.markdown(f"Scrapped WIP Loss: **£{eco_result['wip_scrap_cost_gbp']:,.2f}**")
        st.markdown(f"Schedule Penalty: **+{eco_result['schedule_lead_time_penalty_days']} Days**")
        st.info(eco_result["recommended_action"])


# ------------------------------------------------------------------------------
# TAB 6: FRIDAY PACKAGE ROLLBACK (TD017)
# ------------------------------------------------------------------------------
with tab_rollback:
    st.markdown("### Friday FP2 Package Rollback & Redundant Inventory Engine (TD017)")
    st.markdown(
        "<p style='color:#94A3B8; font-size:12px; margin-top:-6px;'>"
        "Calculates unexpected financial shock and automated write-offs under Article 4.1(f)(i)(C)."
        "</p>",
        unsafe_allow_html=True
    )

    r_col1, r_col2 = st.columns([1, 1])
    with r_col1:
        failed_pkg = st.selectbox("Aero Package for Rollback", ["W16 Slotted Floor Upgrade (Rev B)", "W16 High-Downforce Beam Wing", "W16 Sidepod Inlet Undercut"])
        units_scrapped = st.number_input("Car Sets Manufactured", min_value=1, max_value=6, value=3)
        unit_cost = st.number_input("Manufactured Unit Cost (£)", min_value=20_000, max_value=300_000, value=175_000, step=10_000)
        freight_cost = st.number_input("Emergency Spares Air Charter Freight (£)", min_value=10_000, max_value=150_000, value=65_000, step=5_000)

        rb_result = rollback_engine.evaluate_upgrade_rollback(
            failed_package_name=failed_pkg,
            units_manufactured=units_scrapped,
            unit_cost_gbp=unit_cost,
            freight_logistics_gbp=freight_cost
        )

    with r_col2:
        st.markdown("**Accounting Impact & Reclassification**")
        st.error(f"Total Rollback Shock: **£{rb_result['total_cost_shock_gbp']:,.2f}** (${rb_result['total_cost_shock_usd']:,.2f} USD)")
        st.markdown(f"Net Scrap Write-off: **£{rb_result['net_scrap_loss_gbp']:,.2f}**")
        st.markdown(f"Statutory Reclassification: **{rb_result['fia_inventory_reclassification']}**")
        st.markdown("**Immediate Recovery Plan**")
        for step in rb_result["operational_recovery_steps"]:
            st.markdown(f"• {step}")


# ------------------------------------------------------------------------------
# TAB 7: MONTE CARLO SEASON RISK SANDBOX
# ------------------------------------------------------------------------------
with tab_monte:
    st.markdown("### Strategic Season Roadmap & Stochastic Headroom Sandbox")
    st.markdown(
        "<p style='color:#94A3B8; font-size:12px; margin-top:-6px;'>"
        "Simulate 24-race cumulative spending, toggle candidate upgrade packages, test major chassis crash shocks, and run 1,000-iteration Monte Carlo distributions."
        "</p>",
        unsafe_allow_html=True
    )

    roadmap_view = st.radio(
        "Simulation Model",
        ["Interactive 24-Race 'What-If' Roadmap", "1,000-Run Stochastic Monte Carlo Sandbox"],
        horizontal=True
    )

    if roadmap_view == "Interactive 24-Race 'What-If' Roadmap":
        rm_col1, rm_col2 = st.columns([1, 2])
        with rm_col1:
            st.markdown("#### 1. Candidate Upgrade Deployments")
            upg_choices = []
            for upg in roadmap_engine.AVAILABLE_UPGRADES:
                checked = st.checkbox(
                    f"{upg['name']} (£{upg['cost_gbp']/1e3:,.0f}k, {upg['laptime_delta_ms']}ms)",
                    value=True,
                    key=f"rm_upg_{upg['id']}"
                )
                if checked:
                    upg_choices.append(upg["id"])

            st.markdown("#### 2. Unforeseen Accident / Crash Shock")
            crash_scenario = st.selectbox(
                "Chassis Damage Scenario",
                list(roadmap_engine.CRASH_SCENARIOS.keys())
            )
            st.caption(roadmap_engine.CRASH_SCENARIOS[crash_scenario]["description"])

        with rm_col2:
            rm_res = roadmap_engine.simulate_season(active_upgrade_ids=upg_choices, crash_scenario_key=crash_scenario)
            df_traj = rm_res["trajectory_df"]

            # Headroom Status Alert
            if rm_res["is_breach"]:
                st.error(f"🚨 **STATUTORY COST CAP BREACH:** Overspend of £{abs(rm_res['final_headroom_gbp']):,.2f} projected at Abu Dhabi! Mandatory upgrade cancellation required under Article 8.")
            elif rm_res["danger_zone"]:
                st.warning(f"⚠️ **DANGER ZONE BUFFER (< £2.0M):** Projected Headroom is £{rm_res['final_headroom_gbp']:,.2f}. High risk of minor overspend breach.")
            else:
                st.success(f"✅ **COMPLIANT SEASON TRAJECTORY:** Projected Year-End Headroom: £{rm_res['final_headroom_gbp']:,.2f} (${rm_res['final_headroom_usd']/1e6:.2f}M USD)")

            # KPI Summary
            kpi_r1, kpi_r2, kpi_r3 = st.columns(3)
            with kpi_r1:
                st.metric("Total Upgrade Spend", f"£{rm_res['total_upgrade_spend_gbp']/1e6:.2f}M")
            with kpi_r2:
                st.metric("Net Lap Time Gained", f"-{rm_res['total_laptime_gain_ms']:.0f} ms")
            with kpi_r3:
                st.metric("Cost per Millisecond", f"£{rm_res['cost_per_ms_overall']:,.0f} / ms")

            # Trajectory Chart
            fig_roadmap = go.Figure()
            fig_roadmap.add_trace(go.Scatter(
                x=df_traj["Grand_Prix"], y=df_traj["Cumulative_Spend_GBP"] / 1e6,
                mode="lines+markers", name="Cumulative Spend (£M)",
                line=dict(color="#00D2BE", width=2.5)
            ))
            fig_roadmap.add_trace(go.Scatter(
                x=df_traj["Grand_Prix"], y=df_traj["Cap_Limit_GBP"] / 1e6,
                mode="lines", name=f"Statutory Ceiling (£{rm_res['statutory_cap_gbp']/1e6:.1f}M)",
                line=dict(color="#EF4444", width=2, dash="dash")
            ))
            fig_roadmap.update_layout(
                title="24-Grand Prix Spend Trajectory vs Statutory Ceiling",
                xaxis_title="Grand Prix", yaxis_title="Cumulative Spend (£ Millions)",
                template="plotly_dark", height=320,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,21,28,0.6)",
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_roadmap, use_container_width=True)

    else:
        mc_col1, mc_col2 = st.columns([1, 2])
        with mc_col1:
            st.markdown("**Stochastic Parameters**")
            sim_races = st.slider("Championship Races Remaining", min_value=4, max_value=24, value=14)
            upgrade_fail_risk = st.slider("Upgrade Package Failure Probability", 0.0, 0.40, 0.15, step=0.05)
            upgrade_shock_cost = st.slider("Failed Upgrade Rollback Cost ($)", 500_000, 2_500_000, 1_200_000, step=100_000)
            
            simulator = SeasonRiskSimulator(
                current_headroom_usd=fin_summary["cost_cap_headroom_usd"],
                remaining_races=sim_races,
                iterations=1000
            )
            sim_res = simulator.run_simulation(
                upgrade_rollback_prob=upgrade_fail_risk,
                upgrade_rollback_cost_usd=upgrade_shock_cost
            )

            st.metric("Expected Crash Damage (Mean)", f"${sim_res['expected_damage_mean_usd']/1e6:.2f}M")
            st.metric("95% Worst-Case Headroom (VaR)", f"${sim_res['p5_worst_case_headroom_usd']/1e6:.2f}M")
            breach_prob = sim_res["prob_any_overspend_pct"]
            st.info(f"Probability of Cost Cap Breach: **{breach_prob:.1f}%**")

        with mc_col2:
            fig_hist = px.histogram(
                x=sim_res["simulated_headrooms"] / 1e6,
                nbins=35,
                color_discrete_sequence=["#00D2BE"],
                title="1,000 Simulated Outcomes: Season-Ending Headroom ($ Millions)",
                labels={"x": "Headroom ($M)", "y": "Frequency"}
            )
            fig_hist.add_vline(x=0.0, line_width=2, line_dash="dash", line_color="#EF4444", annotation_text="Breach ($0)")
            fig_hist.update_layout(
                template="plotly_dark", height=350,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,21,28,0.6)",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_hist, use_container_width=True)


# ------------------------------------------------------------------------------
# TAB 8: FIA STATUTORY AUDIT & PDF EXPORT
# ------------------------------------------------------------------------------
with tab_fin:
    st.markdown("### Statutory Cost Cap Reconciliation & Audit Pack Export (Issue 24)")
    st.markdown(
        "<p style='color:#94A3B8; font-size:12px; margin-top:-6px;'>"
        "Audited reconciliation from General Ledger Gross Costs to certified Relevant Costs under Articles 2, 3, & 4."
        "</p>",
        unsafe_allow_html=True
    )

    gross = fin_summary["gross_expenses_usd"]
    excl = fin_summary["excluded_expenses_usd"]
    used_inv = fin_summary["used_inventory_added_usd"]
    red_inv = fin_summary["redundant_inventory_written_off_usd"]
    net_rel = fin_summary["net_relevant_costs_usd"]

    fig_waterfall = go.Figure(go.Waterfall(
        name="FIA Cost Cap Reconciliation",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Gross Expenses", "Art. 3 Exclusions", "TD017 Used Inv.", "TD017 Redundant Inv.", "Net Relevant Costs"],
        textposition="outside",
        text=[f"${gross/1e6:.1f}M", f"-${excl/1e6:.1f}M", f"+${used_inv/1e6:.1f}M", f"+${red_inv/1e6:.1f}M", f"${net_rel/1e6:.1f}M"],
        y=[gross, -excl, used_inv, red_inv, net_rel],
        connector={"line": {"color": "#64748B"}},
        decreasing={"marker": {"color": "#00D2BE"}},
        increasing={"marker": {"color": "#EF4444"}},
        totals={"marker": {"color": "#3B82F6"}}
    ))
    fig_waterfall.update_layout(
        title="Statutory Reconciliation Waterfall (USD Millions)",
        template="plotly_dark", height=360,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,21,28,0.6)",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

    st.markdown("---")
    st.markdown("### Official Compliance Dossier Downloads")

    df_excl = processed_expenses[processed_expenses["is_excluded"] == 1]
    pdf_bytes = pdf_generator.generate_pdf_bytes(fin_summary, df_excl, df_personnel)

    pdf_col1, pdf_col2 = st.columns(2)
    with pdf_col1:
        st.download_button(
            label="📄 Download Official FIA Compliance Dossier (PDF)",
            data=pdf_bytes,
            file_name="FIA_Cost_Cap_Compliance_Dossier_Mercedes_Issue24.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with pdf_col2:
        audit_md = audit_generator.generate_markdown_audit_report(fin_summary, df_excl, df_parts, df_personnel)
        st.download_button(
            label="📝 Download Compliance Dossier (Markdown Format)",
            data=audit_md,
            file_name="FIA_Cost_Cap_Compliance_Dossier_Mercedes_Issue24.md",
            mime="text/markdown",
            use_container_width=True
        )

    st.markdown("---")
    st.markdown("### 📋 Brackley Operations Room // Executive Strategy Debrief")
    st.markdown(
        "<p style='color:#94A3B8; font-size:12px; margin-top:-6px;'>"
        "Generates formal C-suite debrief memo formatted for Toto Wolff (Team Principal & CEO), Chief Financial Officer, and Technical Director."
        "</p>",
        unsafe_allow_html=True
    )

    if st.button("Generate Brackley Operations Memo", key="btn_gen_memo"):
        memo_dict = briefing_generator.generate_memo(
            session_name="Silverstone GP FP1 / Correlation Intercept",
            cci=0.91,
            gate3_locked=False,
            sunk_cost_saved_gbp=450000.0,
            certified_headroom_gbp=fin_summary["cost_cap_headroom_gbp"],
            statutory_cap_gbp=fin_summary["statutory_cap_gbp"],
            blocked_rig_count=blocked_count,
            cell_oee_pct=92.4,
            active_upgrade_name="W16 Spec-B Venturi Floor"
        )
        st.markdown(memo_dict["markdown_memo"])
        st.download_button(
            "📥 Download Executive Debrief (Markdown)",
            data=memo_dict["markdown_memo"],
            file_name=f"Brackley_Ops_Memo_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )

    with st.expander("Preview Formal Statutory Dossier"):
        st.markdown(audit_md)
