"""
src/database.py
Relational Database Architecture & Query Layer
Database: SQLite (f1_operations.db)
"""

import sqlite3
import os
from contextlib import contextmanager
import pandas as pd

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "f1_operations.db")


@contextmanager
def get_db_connection(db_path=DEFAULT_DB_PATH):
    """Context manager for SQLite connections with auto-commit/rollback."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database(db_path=DEFAULT_DB_PATH):
    """Creates the normalized relational tables according to FIA Issue 24 requirements."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. dim_facilities
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_facilities (
            facility_id TEXT PRIMARY KEY,
            facility_name TEXT NOT NULL,
            facility_type TEXT NOT NULL,
            hourly_cost_gbp REAL NOT NULL,
            is_capex_restricted INTEGER NOT NULL DEFAULT 0,
            location TEXT DEFAULT 'Brackley, UK'
        );
        """)

        # 2. dim_parts
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_parts (
            part_id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT UNIQUE NOT NULL,
            revision TEXT NOT NULL DEFAULT 'Rev A',
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            unit_cost_usd REAL NOT NULL,
            unit_cost_gbp REAL NOT NULL,
            lead_time_days INTEGER NOT NULL,
            autoclave_hours REAL NOT NULL DEFAULT 0.0,
            inventory_status TEXT NOT NULL CHECK(inventory_status IN ('Used', 'Unused', 'Redundant')),
            first_used_date TEXT,
            is_critical_path INTEGER NOT NULL DEFAULT 0
        );
        """)

        # 3. fact_test_runs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_test_runs (
            test_id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_reference TEXT UNIQUE NOT NULL,
            facility_id TEXT NOT NULL,
            programme_type TEXT NOT NULL,
            scheduled_start TEXT NOT NULL,
            scheduled_end TEXT NOT NULL,
            actual_status TEXT NOT NULL CHECK(actual_status IN ('Scheduled', 'Running', 'Blocked', 'Completed', 'Cancelled')),
            critical_part_id INTEGER,
            idle_hours REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (facility_id) REFERENCES dim_facilities(facility_id),
            FOREIGN KEY (critical_part_id) REFERENCES dim_parts(part_id)
        );
        """)

        # 4. fact_expenses
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            voucher_ref TEXT UNIQUE NOT NULL,
            reporting_year INTEGER NOT NULL,
            date_incurred TEXT NOT NULL,
            cost_centre TEXT NOT NULL,
            account_desc TEXT NOT NULL,
            amount_usd REAL NOT NULL,
            amount_gbp REAL NOT NULL,
            is_capex INTEGER NOT NULL DEFAULT 0,
            is_excluded INTEGER NOT NULL DEFAULT 0,
            exclusion_clause TEXT DEFAULT NULL,
            test_id INTEGER,
            FOREIGN KEY (test_id) REFERENCES fact_test_runs(test_id)
        );
        """)

        # 5. dim_personnel_td045 (Article 3.1(h) Applied Science vs F1 Split)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_personnel_td045 (
            employee_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            department TEXT NOT NULL,
            total_remuneration_gbp REAL NOT NULL,
            f1_allocation_pct REAL NOT NULL CHECK(f1_allocation_pct BETWEEN 0.0 AND 1.0),
            applied_science_allocation_pct REAL NOT NULL CHECK(applied_science_allocation_pct BETWEEN 0.0 AND 1.0),
            notes TEXT
        );
        """)

        # 6. fact_correlation_runs (Simulation-to-Track Telemetry Comparisons)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_correlation_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            component_name TEXT NOT NULL,
            test_date TEXT NOT NULL,
            tunnel_downforce_kn REAL NOT NULL,
            track_downforce_kn REAL NOT NULL,
            tunnel_drag_kn REAL NOT NULL,
            track_drag_kn REAL NOT NULL,
            front_ride_height_mm REAL NOT NULL,
            rear_ride_height_mm REAL NOT NULL,
            cci_score REAL NOT NULL,
            stage_gate_status TEXT NOT NULL CHECK(stage_gate_status IN ('Approved', 'Warning', 'Locked'))
        );
        """)

        # 7. candidate_upgrades (Pareto Frontier Multi-Objective Evaluation)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_upgrades (
            upgrade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            upgrade_code TEXT UNIQUE NOT NULL,
            target_component TEXT NOT NULL,
            projected_downforce_gain REAL NOT NULL,  -- points of downforce
            lap_time_delta_sec REAL NOT NULL,        -- seconds per lap (negative is faster)
            manufacturing_cost_gbp REAL NOT NULL,
            autoclave_hours REAL NOT NULL,
            lead_time_days INTEGER NOT NULL,
            correlation_risk_score REAL NOT NULL,    -- 0 to 1 (lower is safer)
            is_pareto_optimal INTEGER NOT NULL DEFAULT 0
        );
        """)


def load_table(table_name, db_path=DEFAULT_DB_PATH):
    """Loads an entire table into a pandas DataFrame."""
    with get_db_connection(db_path) as conn:
        return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)


def execute_query(query, params=(), db_path=DEFAULT_DB_PATH):
    """Executes a custom SQL query and returns a pandas DataFrame."""
    with get_db_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)
