"""
src/monte_carlo.py
Stochastic Monte Carlo Risk Simulator for Formula 1 Season Forecasting
Models: Random Crash Damage + Upgrade Failure Rollbacks against FIA Cost Cap Headroom
"""

import numpy as np
import pandas as pd


class SeasonRiskSimulator:
    def __init__(self, current_headroom_usd, remaining_races=14, iterations=1000, random_seed=44):
        self.headroom_usd = current_headroom_usd
        self.remaining_races = remaining_races
        self.iterations = iterations
        self.random_seed = random_seed

    def run_simulation(self, upgrade_rollback_prob=0.15, upgrade_rollback_cost_usd=1_200_000):
        """
        Executes 1,000 season simulations.
        
        Per Race Crash Probability Distribution (Historical F1 Benchmark):
        - Clean Weekend (0 USD): 45%
        - Minor Damage (Front wing/endplate, brake ducts - $180,000): 35%
        - Moderate Damage (Floor, suspension corners, sidepod - $550,000): 15%
        - Severe Crash (Chassis, gearbox casing, engine impact - $1,400,000): 5%
        """
        np.random.seed(self.random_seed)

        damage_levels = [0.0, 180_000.0, 550_000.0, 1_400_000.0]
        damage_probs = [0.45, 0.35, 0.15, 0.05]

        simulated_end_headrooms = []
        total_damages = []
        minor_breaches = 0
        material_breaches = 0

        minor_breach_threshold_usd = 0.0  # Headroom < 0 means overspend
        material_breach_threshold_usd = -(135_000_000 * 0.05)  # Overspend >= 5%

        for _ in range(self.iterations):
            # 1. Simulate crash damage across remaining races
            race_damages = np.random.choice(damage_levels, size=self.remaining_races, p=damage_probs)
            season_crash_total = np.sum(race_damages)

            # 2. Simulate upgrade failure risk (e.g. 1 major aero upgrade package tested)
            failed_upgrade = np.random.rand() < upgrade_rollback_prob
            season_rollback_cost = upgrade_rollback_cost_usd if failed_upgrade else 0.0

            total_cost_shock = season_crash_total + season_rollback_cost
            ending_headroom = self.headroom_usd - total_cost_shock

            simulated_end_headrooms.append(ending_headroom)
            total_damages.append(total_cost_shock)

            if ending_headroom < minor_breach_threshold_usd:
                if ending_headroom <= material_breach_threshold_usd:
                    material_breaches += 1
                else:
                    minor_breaches += 1

        simulated_end_headrooms = np.array(simulated_end_headrooms)
        total_damages = np.array(total_damages)

        p5_worst_case = np.percentile(simulated_end_headrooms, 5)   # 95% confidence worst-case
        p50_median = np.percentile(simulated_end_headrooms, 50)     # Median expected outcome
        p95_best_case = np.percentile(simulated_end_headrooms, 95)  # 95% confidence best-case

        prob_minor_breach = (minor_breaches / self.iterations) * 100.0
        prob_material_breach = (material_breaches / self.iterations) * 100.0
        prob_any_breach = prob_minor_breach + prob_material_breach

        return {
            "iterations": self.iterations,
            "remaining_races": self.remaining_races,
            "initial_headroom_usd": round(self.headroom_usd, 2),
            "expected_damage_mean_usd": round(float(np.mean(total_damages)), 2),
            "median_ending_headroom_usd": round(float(p50_median), 2),
            "p5_worst_case_headroom_usd": round(float(p5_worst_case), 2),
            "p95_best_case_headroom_usd": round(float(p95_best_case), 2),
            "prob_any_overspend_pct": round(prob_any_breach, 2),
            "prob_minor_breach_pct": round(prob_minor_breach, 2),
            "prob_material_breach_pct": round(prob_material_breach, 2),
            "simulated_headrooms": simulated_end_headrooms
        }
