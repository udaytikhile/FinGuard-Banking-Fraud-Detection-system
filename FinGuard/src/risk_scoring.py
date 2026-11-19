"""
FinGuard - Banking Fraud Detection & Transaction Intelligence System
Module: risk_scoring.py
Purpose: Translates raw model probabilities into standardized 0-100 Fraud Risk Scores,
         applies configurable 3-tier risk stratification (Low, Medium, High),
         and generates the Investigation Priority Queue for compliance analysts.
"""

from __future__ import annotations
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd


# Default configurable risk tier thresholds
DEFAULT_CONFIG = {
    "low_threshold": 40.0,    # Scores < 40 = Low Risk
    "high_threshold": 75.0,   # Scores >= 75 = High Risk
    "model_calibrated_threshold": 0.20,  # Boundary mapped to High Risk
    "medium_boundary_prob": 0.05,        # Boundary mapped to Medium Risk
}


def load_model_package(model_path: str | Path) -> Dict[str, Any]:
    """Loads serialized model artifact containing weights, scaler, and parameters."""
    path = Path(model_path)
    if not path.is_file():
        raise FileNotFoundError(f"Model package not found at: {path.resolve()}")
    artifact = joblib.load(path)
    return artifact


def calculate_risk_score(
    probabilities: np.ndarray,
    config: Optional[Dict[str, float]] = None,
) -> np.ndarray:
    """
    Transforms raw model output probabilities into a continuous 0-100 Risk Score.
    Uses calibrated piecewise scaling ensuring transactions exceeding the model's
    operational threshold (0.20) map directly into the High Risk tier (>= 75.0).
    
    Calibration Mapping:
      - P in [0.00, 0.05) -> Score in [0, 40)   [Low Risk: Auto-Cleared]
      - P in [0.05, 0.20) -> Score in [40, 75)  [Medium Risk: Secondary OTP]
      - P in [0.20, 1.00] -> Score in [75, 100] [High Risk: Priority Investigation]
    """
    cfg = DEFAULT_CONFIG if config is None else config
    p_med = cfg["medium_boundary_prob"]
    p_high = cfg["model_calibrated_threshold"]
    s_med = cfg["low_threshold"]
    s_high = cfg["high_threshold"]

    scores = np.zeros_like(probabilities, dtype=float)

    # Segment 1: Low Risk
    mask_low = probabilities < p_med
    scores[mask_low] = (probabilities[mask_low] / p_med) * s_med

    # Segment 2: Medium Risk
    mask_med = (probabilities >= p_med) & (probabilities < p_high)
    scores[mask_med] = s_med + ((probabilities[mask_med] - p_med) / (p_high - p_med)) * (s_high - s_med)

    # Segment 3: High Risk
    mask_high = probabilities >= p_high
    scores[mask_high] = s_high + ((probabilities[mask_high] - p_high) / (1.0 - p_high)) * (100.0 - s_high)

    return np.clip(np.round(scores, 1), 0.0, 100.0)


def assign_risk_tiers(
    scores: np.ndarray,
    config: Optional[Dict[str, float]] = None,
) -> Tuple[List[str], List[str]]:
    """
    Categorizes numeric risk scores into business risk tiers and operational statuses.
    Enforces ethical disclaimer: High Risk is an investigation priority, NOT proof of fraud.
    """
    cfg = DEFAULT_CONFIG if config is None else config
    low_th = cfg["low_threshold"]
    high_th = cfg["high_threshold"]

    categories = []
    statuses = []

    for s in scores:
        if s >= high_th:
            categories.append("High Risk")
            statuses.append("Pending Triage - High Priority")
        elif s >= low_th:
            categories.append("Medium Risk")
            statuses.append("Secondary Verification Required")
        else:
            categories.append("Low Risk")
            statuses.append("Auto-Cleared / Normal")

    return categories, statuses


def score_transactions(
    df: pd.DataFrame,
    model_artifact: Dict[str, Any],
    config: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """
    Applies fitted preprocessor and model to entire transaction stream,
    computing probabilities, 0-100 risk scores, and operational triage tiers.
    """
    model = model_artifact["model"]
    scaler = model_artifact["scaler"]
    feature_cols = model_artifact["feature_cols"]
    scale_cols = model_artifact.get("scale_cols", ["Amount", "Time"])

    # Prepare features
    X = df[feature_cols].copy()
    if scale_cols:
        X[scale_cols] = scaler.transform(X[scale_cols])

    # Predict probabilities
    probabilities = model.predict_proba(X)[:, 1]

    # Calculate calibrated risk scores and tiers
    scores = calculate_risk_score(probabilities, config)
    categories, statuses = assign_risk_tiers(scores, config)

    # Assemble enriched output DataFrame
    df_scored = df.copy()
    df_scored["Fraud_Probability"] = np.round(probabilities, 4)
    df_scored["Fraud_Risk_Score"] = scores
    df_scored["Risk_Category"] = categories
    df_scored["Investigation_Status"] = statuses

    return df_scored


def generate_investigation_priority_queue(
    df_scored: pd.DataFrame,
    output_path: str | Path,
    min_score: float = 75.0,
) -> pd.DataFrame:
    """
    Extracts, ranks, and exports the high-risk transaction queue for fraud analysts.
    Sorted in descending order of risk score and transaction amount.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    high_risk_mask = df_scored["Fraud_Risk_Score"] >= min_score
    queue_cols = [
        "Transaction_ID",
        "Day",
        "Hour",
        "Amount",
        "Fraud_Probability",
        "Fraud_Risk_Score",
        "Risk_Category",
        "Investigation_Status",
        "Class",
    ]
    queue_df = df_scored.loc[high_risk_mask, queue_cols].sort_values(
        by=["Fraud_Risk_Score", "Amount"],
        ascending=[False, False],
    ).reset_index(drop=True)

    queue_df.to_csv(path, index=False)
    return queue_df


def compute_tier_summary(df_scored: pd.DataFrame) -> pd.DataFrame:
    """Aggregates volume, fraud counts, precision, and financial exposure across risk tiers."""
    summary = df_scored.groupby("Risk_Category", as_index=False).agg(
        Total_Transactions=("Transaction_ID", "count"),
        Fraud_Count=("Class", "sum"),
        Total_Exposure_EUR=("Amount", "sum"),
        Fraud_Exposure_EUR=("Amount", lambda x: x[df_scored.loc[x.index, "Class"] == 1].sum()),
        Avg_Risk_Score=("Fraud_Risk_Score", "mean"),
    )

    total_txns = len(df_scored)
    total_fraud = int(df_scored["Class"].sum())
    total_amt = float(df_scored["Amount"].sum())

    summary["Volume_Share_Pct"] = np.round((summary["Total_Transactions"] / total_txns) * 100.0, 3)
    summary["Fraud_Detection_Rate_Pct"] = np.round((summary["Fraud_Count"] / total_fraud) * 100.0, 2)
    summary["Tier_Precision_Pct"] = np.round((summary["Fraud_Count"] / summary["Total_Transactions"]) * 100.0, 2)
    summary["Exposure_Share_Pct"] = np.round((summary["Fraud_Exposure_EUR"] / summary["Total_Exposure_EUR"]) * 100.0, 2)
    summary["Avg_Risk_Score"] = np.round(summary["Avg_Risk_Score"], 1)

    # Order by risk severity
    tier_order = {"High Risk": 1, "Medium Risk": 2, "Low Risk": 3}
    summary["Sort_Key"] = summary["Risk_Category"].map(tier_order)
    summary = summary.sort_values(by="Sort_Key").drop(columns=["Sort_Key"]).reset_index(drop=True)

    return summary


def run_risk_scoring_pipeline(
    data_path: str | Path,
    model_path: str | Path,
    output_scored_path: str | Path,
    output_queue_path: str | Path,
) -> Dict[str, Any]:
    """Runs end-to-end scoring, tier generation, queue export, and portfolio summary."""
    print("[FinGuard Risk] Loading model artifact...", flush=True)
    artifact = load_model_package(model_path)

    print("[FinGuard Risk] Loading cleaned dataset...", flush=True)
    df = pd.read_csv(data_path)

    print(f"[FinGuard Risk] Scoring {len(df):,} transactions...", flush=True)
    t0 = time.time()
    df_scored = score_transactions(df, artifact)
    print(f"[FinGuard Risk] Scoring completed in {time.time() - t0:.2f}s.", flush=True)

    # Save complete scored transactions
    scored_file = Path(output_scored_path)
    scored_file.parent.mkdir(parents=True, exist_ok=True)
    print(f"[FinGuard Risk] Exporting scored dataset to: {scored_file.resolve()}", flush=True)
    df_scored.to_csv(scored_file, index=False)

    # Save high-priority investigation queue
    queue_file = Path(output_queue_path)
    print(f"[FinGuard Risk] Exporting priority queue to: {queue_file.resolve()}", flush=True)
    queue_df = generate_investigation_priority_queue(df_scored, queue_file)

    # Compute risk tier portfolio summary
    tier_summary = compute_tier_summary(df_scored)

    return {
        "total_scored": len(df_scored),
        "high_risk_count": len(queue_df),
        "tier_summary": tier_summary,
        "queue_preview": queue_df.head(10),
    }


if __name__ == "__main__":
    clean_csv = Path("FinGuard/data/processed/clean_creditcard.csv")
    model_file = Path("FinGuard/data/processed/best_model.joblib")
    scored_csv = Path("FinGuard/data/processed/scored_transactions.csv")
    queue_csv = Path("FinGuard/data/processed/investigation_priority_queue.csv")

    if not clean_csv.exists() or not model_file.exists():
        print("Error: Missing prerequisites. Please run earlier pipeline steps.")
        sys.exit(1)

    res = run_risk_scoring_pipeline(clean_csv, model_file, scored_csv, queue_csv)
    print("\n=== Risk Scoring Portfolio Breakdown ===")
    print(res["tier_summary"].to_string(index=False))
    print(f"\nTotal High-Risk Transactions Queued for Investigation: {res['high_risk_count']:,}")
    print("\nTop 5 Priority Investigation Tickets:")
    print(res["queue_preview"].head(5)[["Transaction_ID", "Day", "Hour", "Amount", "Fraud_Risk_Score", "Risk_Category", "Investigation_Status"]].to_string(index=False))

