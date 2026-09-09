"""
tests/test_anomaly.py
Unit tests for Machine Learning Test Rig Telemetry Anomaly Detector
"""

import numpy as np
import pandas as pd
from src.rig_anomaly_detector import RigTelemetryAnomalyDetector


def test_rig_telemetry_anomaly_detection():
    detector = RigTelemetryAnomalyDetector(contamination=0.05, random_state=44)
    
    # 1. Generate nominal baseline telemetry
    np.random.seed(44)
    n_samples = 150
    df_nominal = pd.DataFrame({
        "bearing_temp_c": np.random.normal(68.0, 2.0, n_samples),
        "vibration_rms_g": np.random.normal(0.45, 0.05, n_samples),
        "oil_pressure_bar": np.random.normal(4.8, 0.15, n_samples),
        "shaft_torque_nm": np.random.normal(320.0, 10.0, n_samples)
    })
    detector.train_baseline(df_nominal)
    assert detector.is_trained == True

    # 2. Inject severe anomalous spike (bearing seizure condition)
    df_stream = pd.DataFrame([
        {"bearing_temp_c": 69.1, "vibration_rms_g": 0.46, "oil_pressure_bar": 4.8, "shaft_torque_nm": 322.0},  # Nominal
        {"bearing_temp_c": 114.5, "vibration_rms_g": 3.85, "oil_pressure_bar": 1.9, "shaft_torque_nm": 580.0}, # CRITICAL ANOMALY
    ])

    results = detector.predict_anomalies(df_stream)
    assert results.iloc[0]["is_anomaly"] == False
    assert results.iloc[1]["is_anomaly"] == True

    report = detector.generate_incident_report(results, facility_id="DYN-01")
    assert report["status"] == "CRITICAL_ANOMALY_DETECTED"
    assert report["triggering_vibration_g"] == 3.85
