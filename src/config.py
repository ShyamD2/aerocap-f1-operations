"""
src/config.py
Formula 1 Statutory & Regulatory Configuration
Baseline: FIA Formula 1 Financial Regulations (Issue 24, 30 April 2025)
Team Perimeter: Mercedes-Benz Grand Prix Limited (Brackley, UK)
"""

# ==============================================================================
# FIA FINANCIAL REGULATIONS (ISSUE 24) STATUTORY CONSTANTS
# ==============================================================================
# Article 2.3: Baseline Cap for 21 Competitions
BASE_COST_CAP_USD = 135_000_000.0
STATUTORY_BASE_COMPETITIONS = 21
PER_COMPETITION_DELTA_USD = 1_800_000.0

# Article 4.1(l): Downward adjustment per Sprint Competition
SPRINT_DEDUCTION_USD = 300_000.0

# Article 40 / Initial Applicable Rates (USD per Foreign Currency Unit)
INITIAL_APPLICABLE_RATE_GBP = 1.2691  # USD / GBP
INITIAL_APPLICABLE_RATE_EUR = 1.0982  # USD / EUR
INITIAL_APPLICABLE_RATE_CHF = 1.0040  # USD / CHF

# Appendix 3: Capital Expenditure Limit (Mercedes-Benz Grand Prix Limited)
# Reporting Periods ending 31 Dec 2025, 2026, 2027, 2028
MERCEDES_CAPEX_LIMIT_USD = 42_000_000.0

# Appendix 2: Eligible Wind Tunnel Capital Expenditure Cumulative Ceiling
WIND_TUNNEL_CAPEX_CEILING_USD = 55_000_000.0

# Article 8: Breach Thresholds
MINOR_OVERSPEND_MAX_PCT = 0.05  # < 5% (Article 8.10)
# >= 5% constitutes Material Overspend Breach (Article 8.12)

# ==============================================================================
# CORRELATION & OPERATIONAL THRESHOLDS (MERCEDES SPECIFIC)
# ==============================================================================
# Correlation Confidence Index (CCI) Stage Gate Thresholds
CCI_MIN_GATE3_RELEASE = 0.85     # Minimum correlation required to release full autoclave manufacturing
CCI_WARNING_THRESHOLD = 0.70     # Warning zone: requires aero validation on 7-post rig
CCI_CRITICAL_CORRELATION = 0.55  # Immediate aerodynamic stall/bouncing alarm

# Test Rig Operating Costs (£ per hour)
FACILITY_HOURLY_COSTS_GBP = {
    "DYN-01": 2400.0,   # High Performance Powertrain Dyno
    "DYN-02": 1800.0,   # Transmission & Driveline Dyno
    "RIG-02": 1200.0,   # 7-Post Dynamic Shaker Rig
    "WT-01": 3500.0,    # 60% Scale Aerodynamic Wind Tunnel (App. 2)
    "STR-04": 850.0,    # Static & Torsional Stress Rig
}

# Autoclave Shop Capacity (Hours / Week)
AUTOCLAVE_MAX_WEEKLY_HOURS = 168.0

# Visual Palette (Mercedes-AMG Petronas F1 Team)
COLOR_PETRONAS_TEAL = "#00A19B"
COLOR_OBSIDIAN_BLACK = "#121212"
COLOR_MERCEDES_SILVER = "#C0C0C0"
COLOR_DARK_SURFACE = "#1E1E1E"
COLOR_ALERT_AMBER = "#FFB800"
COLOR_CRITICAL_RED = "#E10600"
COLOR_ACCENT_BLUE = "#0070F3"
