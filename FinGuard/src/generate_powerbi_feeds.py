"""
FinGuard - Banking Fraud Detection & Transaction Intelligence System
Script: generate_powerbi_feeds.py
Purpose: Generates pre-aggregated, optimized CSV datasets for immediate Power BI ingestion.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd


def generate_feeds(scored_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(scored_path)

    # 1. Page 1 Executive KPIs
    tot_txns = len(df)
    fraud_txns = int(df["Class"].sum())
    legit_txns = tot_txns - fraud_txns
    fraud_rate = (fraud_txns / tot_txns) * 100.0
    tot_amt = float(df["Amount"].sum())
    fraud_amt = float(df.loc[df["Class"] == 1, "Amount"].sum())
    legit_amt = tot_amt - fraud_amt

    kpis = pd.DataFrame([
        {"Metric": "Total Transactions", "Value": tot_txns, "Formatted_Value": f"{tot_txns:,}", "Unit": "Count"},
        {"Metric": "Fraud Transactions", "Value": fraud_txns, "Formatted_Value": f"{fraud_txns:,}", "Unit": "Count"},
        {"Metric": "Legitimate Transactions", "Value": legit_txns, "Formatted_Value": f"{legit_txns:,}", "Unit": "Count"},
        {"Metric": "Fraud Rate", "Value": round(fraud_rate, 4), "Formatted_Value": f"{fraud_rate:.4f}%", "Unit": "Percentage"},
        {"Metric": "Total Transaction Amount", "Value": round(tot_amt, 2), "Formatted_Value": f"€{tot_amt:,.2f}", "Unit": "EUR"},
        {"Metric": "Fraud Transaction Amount", "Value": round(fraud_amt, 2), "Formatted_Value": f"€{fraud_amt:,.2f}", "Unit": "EUR"},
        {"Metric": "Legitimate Transaction Amount", "Value": round(legit_amt, 2), "Formatted_Value": f"€{legit_amt:,.2f}", "Unit": "EUR"},
    ])
    kpis.to_csv(output_dir / "page1_executive_kpis.csv", index=False)

    # 2. Hourly Volume & Fraud Velocity
    hourly = df.groupby("Hour").agg(
        Total_Transactions=("Class", "count"),
        Fraud_Transactions=("Class", "sum"),
        Total_Amount_EUR=("Amount", "sum"),
        Fraud_Amount_EUR=("Amount", lambda x: x[df.loc[x.index, "Class"] == 1].sum()),
    ).reset_index()
    hourly["Fraud_Rate_Pct"] = np.round((hourly["Fraud_Transactions"] / hourly["Total_Transactions"]) * 100.0, 4)
    hourly["Total_Amount_EUR"] = np.round(hourly["Total_Amount_EUR"], 2)
    hourly["Fraud_Amount_EUR"] = np.round(hourly["Fraud_Amount_EUR"], 2)
    hourly.to_csv(output_dir / "hourly_volume_and_fraud.csv", index=False)

    # 3. Amount Tier Distribution
    def categorize_amount(amt: float) -> str:
        if amt < 25.0:
            return "1. Under €25"
        elif amt < 100.0:
            return "2. €25 - €99.99"
        elif amt < 300.0:
            return "3. €100 - €299.99"
        elif amt < 1000.0:
            return "4. €300 - €999.99"
        else:
            return "5. €1,000+"

    df["Amount_Bracket"] = df["Amount"].apply(categorize_amount)
    amount_tiers = df.groupby("Amount_Bracket").agg(
        Transaction_Volume=("Class", "count"),
        Fraud_Count=("Class", "sum"),
        Total_Volume_EUR=("Amount", "sum"),
        Fraud_Exposure_EUR=("Amount", lambda x: x[df.loc[x.index, "Class"] == 1].sum()),
    ).reset_index()
    amount_tiers["Fraud_Rate_Pct"] = np.round((amount_tiers["Fraud_Count"] / amount_tiers["Transaction_Volume"]) * 100.0, 4)
    amount_tiers["Total_Volume_EUR"] = np.round(amount_tiers["Total_Volume_EUR"], 2)
    amount_tiers["Fraud_Exposure_EUR"] = np.round(amount_tiers["Fraud_Exposure_EUR"], 2)
    amount_tiers = amount_tiers.sort_values(by="Amount_Bracket").reset_index(drop=True)
    amount_tiers.to_csv(output_dir / "amount_tier_distribution.csv", index=False)

    # 4. Risk Intelligence Summary
    risk_summary = df.groupby("Risk_Category").agg(
        Total_Transactions=("Class", "count"),
        Fraud_Count=("Class", "sum"),
        Total_Exposure_EUR=("Amount", "sum"),
        Fraud_Exposure_EUR=("Amount", lambda x: x[df.loc[x.index, "Class"] == 1].sum()),
        Avg_Risk_Score=("Fraud_Risk_Score", "mean"),
    ).reset_index()
    risk_summary["Detection_Rate_Pct"] = np.round((risk_summary["Fraud_Count"] / fraud_txns) * 100.0, 2)
    risk_summary["Tier_Precision_Pct"] = np.round((risk_summary["Fraud_Count"] / risk_summary["Total_Transactions"]) * 100.0, 2)
    risk_summary["Avg_Risk_Score"] = np.round(risk_summary["Avg_Risk_Score"], 1)
    risk_summary["Total_Exposure_EUR"] = np.round(risk_summary["Total_Exposure_EUR"], 2)
    risk_summary["Fraud_Exposure_EUR"] = np.round(risk_summary["Fraud_Exposure_EUR"], 2)
    risk_summary.to_csv(output_dir / "risk_intelligence_summary.csv", index=False)

    # 5. Investigation Queue Feed (Top 500 High-Risk for Table visualization)
    high_risk_feed = df[df["Fraud_Risk_Score"] >= 75.0][
        ["Transaction_ID", "Day", "Hour", "Amount", "Fraud_Probability", "Fraud_Risk_Score", "Risk_Category", "Investigation_Status", "Class"]
    ].sort_values(by=["Fraud_Risk_Score", "Amount"], ascending=[False, False])
    high_risk_feed.to_csv(output_dir / "investigation_queue_feed.csv", index=False)

    print(f"[PowerBI Feeds] Successfully exported 5 datasets to {output_dir.resolve()}")


if __name__ == "__main__":
    scored_csv = Path("FinGuard/data/processed/scored_transactions.csv")
    out_dir = Path("FinGuard/powerbi/data")
    generate_feeds(scored_csv, out_dir)

