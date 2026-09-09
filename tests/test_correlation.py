"""
tests/test_correlation.py
Unit tests for Simulation-to-Track Correlation Confidence Index (CCI) Engine
"""

import pytest
import numpy as np
from src.correlation_engine import CorrelationEngine


def test_perfect_correlation():
    engine = CorrelationEngine()
    # Identical wind tunnel and track telemetry
    tunnel_df = np.array([10.0, 12.0, 14.0, 16.0])
    track_df = np.array([10.0, 12.0, 14.0, 16.0])
    tunnel_dr = np.array([2.0, 2.5, 3.0, 3.5])
    track_dr = np.array([2.0, 2.5, 3.0, 3.5])
    ride_heights = np.array([15.0, 20.0, 25.0, 30.0])

    res = engine.calculate_cci(tunnel_df, track_df, tunnel_dr, track_dr, ride_heights)
    assert res["cci_score"] >= 0.95
    assert res["stage_gate_status"] == "Approved"


def test_critical_correlation_failure():
    engine = CorrelationEngine()
    # Severe divergence: tunnel predicts high downforce, track experiences detachment
    tunnel_df = np.array([18.0, 20.0, 22.0, 24.0])
    track_df = np.array([10.0, 9.0, 8.0, 7.0])  # Inverse gradient (porpoising/detachment)
    tunnel_dr = np.array([3.0, 3.5, 4.0, 4.5])
    track_dr = np.array([5.0, 6.0, 7.0, 8.0])
    ride_heights = np.array([15.0, 20.0, 25.0, 30.0])

    res = engine.calculate_cci(tunnel_df, track_df, tunnel_dr, track_dr, ride_heights)
    assert res["cci_score"] < 0.70
    assert res["stage_gate_status"] == "Locked"
