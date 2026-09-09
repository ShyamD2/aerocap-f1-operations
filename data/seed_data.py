"""
data/seed_data.py
Database Seeder for F1-OpsCorrelate Platform
Populates SQLite database (data/f1_operations.db) with realistic telemetry, parts, and expenses.
"""

import os
import sys
import random
from datetime import datetime, timedelta

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from src.database import get_db_connection, initialize_database, DEFAULT_DB_PATH
from src.config import INITIAL_APPLICABLE_RATE_GBP


def seed_all(db_path=DEFAULT_DB_PATH):
    print(f"[SEED] Initializing database schema at: {db_path}")
    initialize_database(db_path)
    random.seed(44)
    np.random.seed(44)

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # Clean existing rows and reset sequence
        for tbl in ["candidate_upgrades", "fact_correlation_runs", "dim_personnel_td045", 
                    "fact_expenses", "fact_test_runs", "dim_parts", "dim_facilities"]:
            cursor.execute(f"DELETE FROM {tbl};")
        try:
            cursor.execute("DELETE FROM sqlite_sequence;")
        except sqlite3.OperationalError:
            pass

        # ----------------------------------------------------------------------
        # 1. SEED: dim_facilities
        # ----------------------------------------------------------------------
        facilities = [
            ("DYN-01", "AVL High Performance Powertrain Dyno", "Dyno", 2400.0, 1, "Brixworth/Brackley"),
            ("DYN-02", "8-Speed Seamless Transmission Rig", "Dyno", 1800.0, 0, "Brackley Building 3"),
            ("RIG-02", "7-Post Dynamic Shaker Rig (Vehicle Dynamics)", "Rig", 1200.0, 0, "Brackley Building 2"),
            ("WT-01", "60% Rolling Road Wind Tunnel (17m2 Nozzle)", "Wind Tunnel", 3500.0, 1, "Brackley Wind Tunnel Complex"),
            ("STR-04", "Full Vehicle Torsional & Crash Test Cell", "Structural Rig", 850.0, 0, "Brackley Composites Shop"),
        ]
        cursor.executemany("""
        INSERT INTO dim_facilities (facility_id, facility_name, facility_type, hourly_cost_gbp, is_capex_restricted, location)
        VALUES (?, ?, ?, ?, ?, ?);
        """, facilities)
        print(f"[SEED] Inserted {len(facilities)} facilities.")

        # ----------------------------------------------------------------------
        # 2. SEED: dim_parts (BOM)
        # ----------------------------------------------------------------------
        categories = ["Aerodynamics", "Suspension", "Chassis_Survival_Cell", "Transmission", "Cooling"]
        parts_data = [
            # Critical parts with specific scenarios
            ("W16-FL-001", "Rev A", "Underfloor Venturi Tunnel Body", "Aerodynamics", 185000.0, 14, 36.0, "Used", "2026-03-01", 1),
            ("W16-FL-002", "Rev B", "Slotted Edge Floor Upgrade (Austin Spec)", "Aerodynamics", 210000.0, 18, 42.0, "Redundant", "2026-05-12", 1),
            ("W16-FW-010", "Rev C", "Front Wing Mainplane & Flaps (Low Downforce)", "Aerodynamics", 95000.0, 9, 20.0, "Used", "2026-04-10", 0),
            ("W16-FW-011", "Rev D", "Front Wing Outwash Endplate Revision", "Aerodynamics", 115000.0, 12, 24.0, "Unused", None, 1),
            ("W16-RW-004", "Rev A", "High Downforce Rear Wing & Beam Wing", "Aerodynamics", 145000.0, 11, 28.0, "Used", "2026-03-01", 0),
            ("W16-SUSP-FR-01", "Rev A", "Front Pushrod Upright & Wishbone Assembly", "Suspension", 78000.0, 7, 12.0, "Used", "2026-03-01", 0),
            ("W16-SUSP-RR-02", "Rev B", "Rear Inboard Pullrod Rocker & Heave Spring", "Suspension", 82000.0, 8, 14.0, "Used", "2026-03-01", 0),
            ("W16-DIFF-003", "Rev A", "Carbon Composite Diffuser Sidewall", "Aerodynamics", 65000.0, 10, 16.0, "Used", "2026-03-01", 0),
            ("W16-SIDE-005", "Rev B", "Undercut Sidepod Inlet Duct", "Aerodynamics", 125000.0, 15, 30.0, "Unused", None, 1),
            ("W16-HALO-001", "Rev A", "Titanium Halo Fairing & Vane", "Chassis_Survival_Cell", 35000.0, 5, 6.0, "Used", "2026-03-01", 0),
        ]

        # Generate 40 additional realistic parts
        for i in range(11, 51):
            cat = random.choice(categories)
            code = f"W16-{cat[:4].upper()}-{i:03d}"
            rev = random.choice(["Rev A", "Rev B", "Rev C"])
            cost_usd = round(random.uniform(15000.0, 140000.0), 2)
            lead = random.randint(3, 22)
            hours = round(random.uniform(4.0, 32.0), 1)
            status = random.choice(["Used", "Used", "Used", "Unused", "Redundant"])
            used_date = "2026-03-15" if status == "Used" else None
            is_crit = 1 if random.random() < 0.25 else 0
            parts_data.append((code, rev, f"{cat} Structural Component {i}", cat, cost_usd, lead, hours, status, used_date, is_crit))

        parts_to_insert = []
        for p in parts_data:
            cost_gbp = round(p[4] / INITIAL_APPLICABLE_RATE_GBP, 2)
            parts_to_insert.append((p[0], p[1], p[2], p[3], p[4], cost_gbp, p[5], p[6], p[7], p[8], p[9]))

        cursor.executemany("""
        INSERT INTO dim_parts (part_number, revision, description, category, unit_cost_usd, unit_cost_gbp, lead_time_days, autoclave_hours, inventory_status, first_used_date, is_critical_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, parts_to_insert)
        print(f"[SEED] Inserted {len(parts_to_insert)} parts in BOM.")

        # Map part numbers to auto-generated part_id for foreign keys
        cursor.execute("SELECT part_id, part_number FROM dim_parts;")
        part_map = {row[1]: row[0] for row in cursor.fetchall()}
        default_part_id = next(iter(part_map.values())) if part_map else None

        # ----------------------------------------------------------------------
        # 3. SEED: fact_test_runs
        # ----------------------------------------------------------------------
        now = datetime.now()
        test_runs = [
            ("TEST-PU-901", "DYN-01", "1000km Engine Durability Cycle", (now + timedelta(days=2)).strftime("%Y-%m-%d 08:00"), (now + timedelta(days=4)).strftime("%Y-%m-%d 18:00"), "Scheduled", part_map.get("W16-FL-001", default_part_id), 0.0),
            ("TEST-AERO-402", "WT-01", "Ride-Height Sensitivity & Yaw Map", (now + timedelta(days=1)).strftime("%Y-%m-%d 06:00"), (now + timedelta(days=2)).strftime("%Y-%m-%d 20:00"), "Running", part_map.get("W16-FW-011", default_part_id), 0.0),
            ("TEST-DYN-805", "DYN-02", "Torque Transfer & Gearshift Transient", (now + timedelta(days=5)).strftime("%Y-%m-%d 09:00"), (now + timedelta(days=7)).strftime("%Y-%m-%d 17:00"), "Scheduled", part_map.get("W16-SUSP-RR-02", default_part_id), 0.0),
            ("TEST-SHAKE-301", "RIG-02", "Kerb Impact & High-Frequency Shaker Run", (now - timedelta(days=3)).strftime("%Y-%m-%d 08:00"), (now - timedelta(days=2)).strftime("%Y-%m-%d 16:00"), "Completed", part_map.get("W16-HALO-001", default_part_id), 0.0),
            ("TEST-STR-104", "STR-04", "Rear Impact Structure Torsional Rigidity", (now + timedelta(days=3)).strftime("%Y-%m-%d 10:00"), (now + timedelta(days=4)).strftime("%Y-%m-%d 14:00"), "Blocked", part_map.get("W16-FL-002", default_part_id), 8.0),
        ]
        cursor.executemany("""
        INSERT INTO fact_test_runs (test_reference, facility_id, programme_type, scheduled_start, scheduled_end, actual_status, critical_part_id, idle_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, test_runs)
        print(f"[SEED] Inserted {len(test_runs)} test runs.")

        # Map test references to auto-generated test_id for foreign keys
        cursor.execute("SELECT test_id, test_reference FROM fact_test_runs;")
        test_map = {row[1]: row[0] for row in cursor.fetchall()}

        # ----------------------------------------------------------------------
        # 4. SEED: fact_expenses
        # ----------------------------------------------------------------------
        expenses = [
            # OpEx Relevant Costs
            ("VOUCH-OP-001", 2026, "2026-01-15", "Composites_Mfg", "Toray T1000 Carbon Fibre Pre-preg Rolls", 4200000.0, 0, 0, None, None),
            ("VOUCH-OP-002", 2026, "2026-02-10", "Test_Operations", "Wind Tunnel Rolling Road Spare Belts & Power", 1850000.0, 0, 0, None, test_map.get("TEST-AERO-402")),
            ("VOUCH-OP-003", 2026, "2026-02-28", "Chassis_Engineering", "Wind Tunnel Rapid Prototyping Resins", 950000.0, 0, 0, None, None),
            ("VOUCH-OP-004", 2026, "2026-03-15", "Race_Operations", "Titanium Fasteners & High-Tensile Hardware", 680000.0, 0, 0, None, None),
            ("VOUCH-OP-005", 2026, "2026-04-05", "Dyno_Engineering", "Dyno Rig Cell Electricity & Chiller Utilities", 1450000.0, 0, 0, None, test_map.get("TEST-PU-901")),
            ("VOUCH-OP-006", 2026, "2026-04-20", "Vehicle_Dynamics", "7-Post Shaker Load Cells & Telemetry Sensors", 320000.0, 0, 0, None, test_map.get("TEST-SHAKE-301")),
            ("VOUCH-OP-007", 2026, "2026-05-01", "Manufacturing", "CNC Machine Tooling & Diamond Cutters", 890000.0, 0, 0, None, None),

            # Statutory Excluded Expenses (Article 3.1)
            ("VOUCH-EX-101", 2026, "2026-01-01", "Executive", "F1 Race Driver Retainer Consideration", 22000000.0, 0, 1, "Art. 3.1(b) F1 Driver Consideration", None),
            ("VOUCH-EX-102", 2026, "2026-01-01", "Executive", "Top 3 Highest Paid Personnel Remuneration", 9500000.0, 0, 1, "Art. 3.1(d) Top 3 Excluded Persons", None),
            ("VOUCH-EX-103", 2026, "2026-02-15", "Marketing", "Silverstone Paddock Club Hospitality Suite", 2800000.0, 0, 1, "Art. 3.1(a) Marketing Activities", None),
            ("VOUCH-EX-104", 2026, "2026-03-01", "Marketing", "Brand Merchandise Production & Global PR", 1400000.0, 0, 1, "Art. 3.1(a) Marketing Activities", None),
            ("VOUCH-EX-105", 2026, "2026-03-20", "Travel_Office", "Trackside Race Team Commercial Flights & Hotels", 3800000.0, 0, 1, "Art. 3.1(r) Personnel Travel & Accommodation", None),
            ("VOUCH-EX-106", 2026, "2026-04-10", "Finance", "Corporate Revolving Credit Facility Interest", 650000.0, 0, 1, "Art. 3.1(f) Finance Costs", None),
            ("VOUCH-EX-107", 2026, "2026-04-15", "Finance", "HMRC UK Corporate Income Tax Payment", 1950000.0, 0, 1, "Art. 3.1(g) Corporate Income Tax", None),
            ("VOUCH-EX-108", 2026, "2026-05-01", "Sustainability", "Brackley Campus Solar PV Farm & Renewable Grid", 850000.0, 0, 1, "Art. 3.1(y) Sustainability Initiative Costs", None),
            ("VOUCH-EX-109", 2026, "2026-05-15", "Heritage_Dept", "Historic W07 Formula 1 Car Demo Run & Restoration", 420000.0, 0, 1, "Art. 3.1(e) Heritage Asset Activities", None),

            # Capital Expenditure (Appendix 3)
            ("VOUCH-CAP-201", 2026, "2026-02-01", "Facilities_CapEx", "MTS Multi-Axis 7-Post Shaker Actuator Upgrade", 4500000.0, 1, 0, None, None),
            ("VOUCH-CAP-202", 2026, "2026-03-10", "Facilities_CapEx", "DMG Mori 5-Axis Precision Gantry Milling Center", 3800000.0, 1, 0, None, None),
            ("VOUCH-CAP-203", 2026, "2026-04-12", "Facilities_CapEx", "Wind Tunnel Model Hexapod Motion System (App 2)", 6200000.0, 1, 0, None, None),
        ]
        
        expenses_to_insert = []
        for e in expenses:
            gbp = round(e[5] / INITIAL_APPLICABLE_RATE_GBP, 2)
            # voucher_ref, reporting_year, date_incurred, cost_centre, account_desc, amount_usd, amount_gbp, is_capex, is_excluded, exclusion_clause, test_id
            expenses_to_insert.append((e[0], e[1], e[2], e[3], e[4], e[5], gbp, e[6], e[7], e[8], e[9]))

        cursor.executemany("""
        INSERT INTO fact_expenses (voucher_ref, reporting_year, date_incurred, cost_centre, account_desc, amount_usd, amount_gbp, is_capex, is_excluded, exclusion_clause, test_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, expenses_to_insert)
        print(f"[SEED] Inserted {len(expenses_to_insert)} ledger expense vouchers.")

        # ----------------------------------------------------------------------
        # 5. SEED: dim_personnel_td045 (Applied Science Time Split)
        # ----------------------------------------------------------------------
        personnel = [
            ("EMP-041", "Dr. Marcus Vance", "Aerodynamics R&D", 320000.0, 0.60, 0.40, "40% allocated to INEOS Britannia America's Cup hydrofoil aero (TD045)"),
            ("EMP-088", "Elena Rostova", "Computational Fluid Dynamics", 210000.0, 0.50, 0.50, "50% allocated to INEOS Grenadiers cycling wind-tunnel testing"),
            ("EMP-112", "Liam Gallagher", "Composites Manufacturing", 165000.0, 0.70, 0.30, "30% allocated to Commercial Marine Composite Fabrication"),
            ("EMP-204", "Julian Brandt", "Structural Dynamics", 195000.0, 0.75, 0.25, "25% allocated to High-Speed Rail aerodynamic shielding"),
        ]
        cursor.executemany("""
        INSERT INTO dim_personnel_td045 (employee_id, full_name, department, total_remuneration_gbp, f1_allocation_pct, applied_science_allocation_pct, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, personnel)
        print(f"[SEED] Inserted {len(personnel)} TD045 cross-allocated personnel.")

        # ----------------------------------------------------------------------
        # 6. SEED: candidate_upgrades (Pareto Frontier Evaluation)
        # ----------------------------------------------------------------------
        candidates = [
            # code, component, downforce points, lap_delta_s, cost_gbp, autoclave_h, lead_days, risk_score
            ("UPG-W16-FL-A", "Underfloor Venturi V2", 18.5, -0.22, 380000.0, 48.0, 16, 0.15), # High DF, high cost
            ("UPG-W16-FL-B", "Slotted Edge Floor (Weight-Optimized)", 12.0, -0.14, 190000.0, 24.0, 9, 0.08),  # Cost effective, fast
            ("UPG-W16-FW-01", "Aggressive Inwash Front Wing", 9.5, -0.10, 140000.0, 18.0, 7, 0.12),
            ("UPG-W16-FW-02", "Low-Drag Beam Wing & Flap", 5.0, -0.06, 75000.0, 10.0, 5, 0.04),
            ("UPG-W16-DIFF-1", "Expanded Throat Diffuser", 14.0, -0.16, 260000.0, 32.0, 12, 0.22),
            ("UPG-W16-SIDE-A", "Aggressive Undercut Sidepod", 7.0, -0.07, 310000.0, 44.0, 19, 0.35), # Dominated: high cost, low gain
            ("UPG-W16-SUSP-A", "Anti-Dive Front Pushrod Geometry", 8.0, -0.11, 160000.0, 16.0, 8, 0.05),
        ]
        cursor.executemany("""
        INSERT INTO candidate_upgrades (upgrade_code, target_component, projected_downforce_gain, lap_time_delta_sec, manufacturing_cost_gbp, autoclave_hours, lead_time_days, correlation_risk_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, candidates)
        print(f"[SEED] Inserted {len(candidates)} candidate upgrades.")

        # ----------------------------------------------------------------------
        # 7. SEED: fact_correlation_runs (Simulation vs Track Telemetry)
        # ----------------------------------------------------------------------
        correlation_runs = [
            ("W16-Baseline-Floor", "2026-03-01", 14.8, 14.5, 3.2, 3.3, 18.0, 48.0, 0.92, "Approved"),
            ("W16-Slotted-Floor-RevB", "2026-05-10", 17.5, 12.1, 3.6, 4.4, 15.0, 42.0, 0.62, "Locked"), # Major correlation drop
            ("W16-Front-Wing-RevC", "2026-04-12", 8.4, 8.2, 1.9, 1.95, 20.0, 50.0, 0.89, "Approved"),
            ("W16-Diffuser-RevA", "2026-03-25", 9.8, 8.7, 2.1, 2.4, 16.5, 45.0, 0.76, "Warning"),
        ]
        cursor.executemany("""
        INSERT INTO fact_correlation_runs (component_name, test_date, tunnel_downforce_kn, track_downforce_kn, tunnel_drag_kn, track_drag_kn, front_ride_height_mm, rear_ride_height_mm, cci_score, stage_gate_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, correlation_runs)
        print(f"[SEED] Inserted {len(correlation_runs)} simulation-to-track correlation runs.")

    print("\n[SUCCESS] Database seeded successfully!")


if __name__ == "__main__":
    seed_all()
