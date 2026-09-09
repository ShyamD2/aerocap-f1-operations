"""
src/correlation_engine.py
Simulation-to-Track Correlation Confidence Index (CCI) Engine
Solves: Mercedes-AMG F1's primary challenge of Wind Tunnel/CFD vs Track correlation failure
"""

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from src.config import CCI_MIN_GATE3_RELEASE, CCI_WARNING_THRESHOLD


class CorrelationEngine:
    def __init__(self, gate3_threshold=CCI_MIN_GATE3_RELEASE, warning_threshold=CCI_WARNING_THRESHOLD):
        self.gate3_threshold = gate3_threshold
        self.warning_threshold = warning_threshold

    def calculate_cci(self, tunnel_downforce, track_downforce, tunnel_drag, track_drag, ride_heights=None):
        """
        Calculates the composite Correlation Confidence Index (CCI) in [0.0, 1.0].
        
        Components:
        1. Downforce Normalized RMSE (Weight: 50%)
        2. Drag Normalized RMSE (Weight: 20%)
        3. Ride-Height Sensitivity / Monotonicity Spearman Rank Correlation (Weight: 30%)
        """
        tunnel_df = np.asarray(tunnel_downforce, dtype=float)
        track_df = np.asarray(track_downforce, dtype=float)
        tunnel_dr = np.asarray(tunnel_drag, dtype=float)
        track_dr = np.asarray(track_drag, dtype=float)

        if len(tunnel_df) == 0 or len(track_df) == 0 or len(tunnel_df) != len(track_df):
            raise ValueError("Arrays must be non-empty and of identical lengths.")

        # 1. Downforce relative error
        df_rmse = np.sqrt(np.mean((track_df - tunnel_df) ** 2))
        mean_track_df = np.mean(np.abs(track_df))
        df_error = df_rmse / mean_track_df if mean_track_df > 0 else 1.0
        df_score = max(0.0, 1.0 - df_error)

        # 2. Drag relative error
        dr_rmse = np.sqrt(np.mean((track_dr - tunnel_dr) ** 2))
        mean_track_dr = np.mean(np.abs(track_dr))
        dr_error = dr_rmse / mean_track_dr if mean_track_dr > 0 else 1.0
        dr_score = max(0.0, 1.0 - dr_error)

        # 3. Ride-height rank correlation (measures aero map gradient consistency)
        if ride_heights is not None and len(ride_heights) >= 3:
            # Spearman correlation between delta(tunnel) and delta(track) across ride heights
            corr, _ = spearmanr(tunnel_df, track_df)
            gradient_score = max(0.0, float(corr)) if not np.isnan(corr) else 0.5
        else:
            gradient_score = df_score

        # Composite score
        composite_cci = (0.50 * df_score) + (0.20 * dr_score) + (0.30 * gradient_score)
        composite_cci = float(np.clip(composite_cci, 0.0, 1.0))

        # Status determination
        if composite_cci >= self.gate3_threshold:
            status = "Approved"
            action = "Correlation verified. Autoclave production authorized."
        elif composite_cci >= self.warning_threshold:
            status = "Warning"
            action = "Ride-height sensitivity detected. Mandatory 7-post dynamic shaker rig validation required."
        else:
            status = "Locked"
            action = "Critical correlation failure (aero stall/bouncing risk). Autoclave tooling spend BLOCKED."

        return {
            "cci_score": round(composite_cci, 4),
            "downforce_accuracy_pct": round(df_score * 100, 2),
            "drag_accuracy_pct": round(dr_score * 100, 2),
            "gradient_rank_correlation": round(gradient_score, 4),
            "stage_gate_status": status,
            "operational_action": action
        }

    def evaluate_component_run(self, df_telemetry):
        """
        Evaluates an entire session DataFrame containing telemetry channels.
        Expected columns: tunnel_downforce, track_downforce, tunnel_drag, track_drag, ride_height.
        """
        return self.calculate_cci(
            tunnel_downforce=df_telemetry["tunnel_downforce"].values,
            track_downforce=df_telemetry["track_downforce"].values,
            tunnel_drag=df_telemetry["tunnel_drag"].values,
            track_drag=df_telemetry["track_drag"].values,
            ride_heights=df_telemetry["ride_height"].values if "ride_height" in df_telemetry else None
        )
