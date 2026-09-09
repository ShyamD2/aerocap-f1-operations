"""
tests/test_fastf1.py
Unit tests for Real-World Track Telemetry & Aerodynamic Load Proxy Engine
"""

from src.fastf1_telemetry import F1TelemetryAnalyzer


def test_silverstone_telemetry_generation():
    analyzer = F1TelemetryAnalyzer(driver="RUS", grand_prix="Silverstone", year=2024)
    df = analyzer.load_telemetry_lap(use_live_api=False)

    required_cols = [
        "distance_m", "speed_kmh", "throttle_pct", "brake_pct",
        "aerodynamic_downforce_kn", "front_ride_height_mm"
    ]
    for col in required_cols:
        assert col in df.columns

    # Verify physical validity of telemetry
    assert df["speed_kmh"].max() > 300.0   # Top speed on Hangar Straight
    assert df["speed_kmh"].min() > 60.0    # Slowest corner (Loop)
    assert df["aerodynamic_downforce_kn"].max() > 20.0  # High-G downforce at 300+ km/h
    assert df["front_ride_height_mm"].min() < 15.0      # High-speed dynamic compression
    assert df["front_ride_height_mm"].max() <= 35.0     # Nominal static ride height


def test_comparative_telemetry_generation():
    analyzer = F1TelemetryAnalyzer(driver="RUS", grand_prix="Silverstone", year=2024)
    comp_res = analyzer.load_comparative_telemetry(driver_a="RUS", driver_b="VER")

    assert "comparison_df" in comp_res
    assert "total_lost_in_mb_ms" in comp_res
    assert "avg_rh_gap_mb_mm" in comp_res
    assert comp_res["total_lost_in_mb_ms"] > 0.0
    assert comp_res["avg_rh_gap_mb_mm"] > 0.0

    df_comp = comp_res["comparison_df"]
    assert "speed_rus" in df_comp.columns
    assert "speed_ver" in df_comp.columns
    assert "ride_height_rus" in df_comp.columns
    assert "ride_height_ver" in df_comp.columns

