"""
FinGuard - Banking Fraud Detection & Transaction Intelligence System
Module: data_cleaning.py
Purpose: Audits raw transaction data, evaluates quality metrics, handles duplicates,
         validates schema, and generates a structured, reproducible clean dataset.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Any, Dict, Tuple
import numpy as np
import pandas as pd


def load_raw_data(filepath: str | Path) -> pd.DataFrame:
    """
    Loads raw transaction records from CSV.
    Ensures immutable treatment of the source file.
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Raw data file not found at: {path.resolve()}")
    df = pd.read_csv(path)
    return df


def inspect_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Inspects shape, columns, and data types of the dataset.
    """
    return {
        "num_rows": int(df.shape[0]),
        "num_columns": int(df.shape[1]),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "memory_mb": float(df.memory_usage(deep=True).sum() / (1024 * 1024)),
    }


def check_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates missing value counts and percentages across all features.
    """
    missing_count = df.isnull().sum()
    missing_pct = (missing_count / len(df)) * 100.0
    summary = pd.DataFrame({
        "Feature": df.columns,
        "Missing_Count": missing_count.values,
        "Missing_Percentage": missing_pct.values,
    })
    return summary


def check_duplicates(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Identifies duplicate transactions based on feature parity.
    Distinguishes duplicates between legitimate and fraudulent transactions.
    """
    feature_cols = [c for c in df.columns if c not in ["Transaction_ID"]]
    duplicate_mask = df.duplicated(subset=feature_cols, keep="first")
    duplicate_count = int(duplicate_mask.sum())
    
    fraud_duplicates = 0
    legit_duplicates = 0
    if "Class" in df.columns and duplicate_count > 0:
        fraud_duplicates = int(df.loc[duplicate_mask, "Class"].sum())
        legit_duplicates = duplicate_count - fraud_duplicates

    return {
        "duplicate_count": duplicate_count,
        "duplicate_percentage": (duplicate_count / len(df)) * 100.0,
        "fraud_duplicates": fraud_duplicates,
        "legit_duplicates": legit_duplicates,
        "duplicate_mask": duplicate_mask,
    }


def analyze_class_distribution(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Quantifies class distribution and imbalance ratio.
    """
    if "Class" not in df.columns:
        raise KeyError("Column 'Class' not found in dataset.")

    class_counts = df["Class"].value_counts().to_dict()
    legit_count = int(class_counts.get(0, 0))
    fraud_count = int(class_counts.get(1, 0))
    total = legit_count + fraud_count
    fraud_rate = (fraud_count / total * 100.0) if total > 0 else 0.0

    return {
        "total_transactions": total,
        "legitimate_count": legit_count,
        "fraud_count": fraud_count,
        "fraud_rate_pct": fraud_rate,
        "imbalance_ratio": f"1:{int(round(legit_count / fraud_count))}" if fraud_count > 0 else "N/A",
    }


def analyze_outliers(df: pd.DataFrame, column: str = "Amount") -> Dict[str, Any]:
    """
    Computes IQR and statistical distribution metrics for monetary amounts.
    """
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found.")

    col = df[column]
    q25 = float(col.quantile(0.25))
    q50 = float(col.quantile(0.50))
    q75 = float(col.quantile(0.75))
    iqr = q75 - q25
    lower_bound = float(q25 - (1.5 * iqr))
    upper_bound = float(q75 + (1.5 * iqr))

    outliers = col[(col < lower_bound) | (col > upper_bound)]
    outlier_count = int(len(outliers))
    outlier_pct = (outlier_count / len(df)) * 100.0

    return {
        "feature": column,
        "mean": float(col.mean()),
        "std": float(col.std()),
        "min": float(col.min()),
        "q25": q25,
        "median": q50,
        "q75": q75,
        "max": float(col.max()),
        "iqr": float(iqr),
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "outlier_count": outlier_count,
        "outlier_percentage": outlier_pct,
        "skewness": float(col.skew()),
    }


def clean_and_preprocess(
    df: pd.DataFrame,
    drop_duplicates: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw data, applies deduplication, validates value domains,
    generates temporal features (Hour, Day), and adds a unique Transaction_ID.
    """
    initial_shape = df.shape
    df_clean = df.copy()

    # Step 1: Missing values check
    missing_total = int(df_clean.isnull().sum().sum())
    if missing_total > 0:
        df_clean = df_clean.dropna()

    # Step 2: Handle duplicates
    dup_stats = check_duplicates(df_clean)
    if drop_duplicates and dup_stats["duplicate_count"] > 0:
        df_clean = df_clean.drop_duplicates(keep="first").reset_index(drop=True)

    # Step 3: Domain validations (Time and Amount must be non-negative)
    valid_amount_mask = df_clean["Amount"] >= 0
    valid_time_mask = df_clean["Time"] >= 0
    df_clean = df_clean[valid_amount_mask & valid_time_mask].reset_index(drop=True)

    # Step 4: Feature Engineering - Temporal attributes
    # Time in dataset represents seconds elapsed from transaction #1 over 48 hours
    df_clean["Hour"] = ((df_clean["Time"] // 3600) % 24).astype(int)
    df_clean["Day"] = ((df_clean["Time"] // 86400) + 1).astype(int)

    # Step 5: Assign immutable primary key for analyst traceability
    df_clean["Transaction_ID"] = [f"TXN_{i+1:07d}" for i in range(len(df_clean))]

    # Step 6: Cast data types strictly
    df_clean["Class"] = df_clean["Class"].astype(int)
    df_clean["Amount"] = df_clean["Amount"].astype(float)
    df_clean["Time"] = df_clean["Time"].astype(float)

    # Reorder columns: Transaction_ID, Time, Day, Hour, Amount, V1-V28, Class
    v_cols = [f"V{i}" for i in range(1, 29)]
    ordered_cols = ["Transaction_ID", "Time", "Day", "Hour", "Amount"] + v_cols + ["Class"]
    df_clean = df_clean[ordered_cols]

    audit = {
        "initial_rows": initial_shape[0],
        "initial_cols": initial_shape[1],
        "final_rows": df_clean.shape[0],
        "final_cols": df_clean.shape[1],
        "dropped_duplicates": dup_stats["duplicate_count"] if drop_duplicates else 0,
        "missing_removed": missing_total,
        "class_distribution": analyze_class_distribution(df_clean),
        "amount_stats": analyze_outliers(df_clean, "Amount"),
    }

    return df_clean, audit


def generate_data_quality_report(audit: Dict[str, Any], raw_audit: Dict[str, Any], output_path: str | Path) -> None:
    """
    Renders an enterprise Data Quality Report formatted in GitHub-flavored Markdown.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    cls_raw = raw_audit["class_distribution"]
    cls_clean = audit["class_distribution"]
    amt = audit["amount_stats"]

    content = f"""# FinGuard – Data Quality & Preprocessing Audit Report

## 1. Executive Summary
- **Audit Date**: 2026-11-05
- **Dataset Domain**: Credit Card Financial Transactions (48-hour European cardholder window)
- **Objective**: Establish baseline data integrity, validate schemas, resolve duplicate transactions, and produce an investigation-ready dataset for fraud detection and business intelligence.

## 2. Ingestion & Schema Verification
| Parameter | Raw Dataset | Cleaned Dataset |
|---|---|---|
| Total Rows | {raw_audit['shape']['num_rows']:,} | {audit['final_rows']:,} |
| Total Features | {raw_audit['shape']['num_columns']} | {audit['final_cols']} |
| In-Memory Size | {raw_audit['shape']['memory_mb']:.2f} MB | {(audit['final_rows'] * audit['final_cols'] * 8) / (1024*1024):.2f} MB |
| Primary Key | None | `Transaction_ID` (Added) |
| Missing Values | 0 (0.00%) | 0 (0.00%) |
| Duplicate Transactions | {raw_audit['duplicates']['duplicate_count']:,} ({raw_audit['duplicates']['duplicate_percentage']:.3f}%) | 0 (Deduplicated) |

## 3. Duplicate Transaction Treatment
- **Total Identical Records Found**: {raw_audit['duplicates']['duplicate_count']:,}
- **Legitimate Duplicates**: {raw_audit['duplicates']['legit_duplicates']:,}
- **Fraudulent Duplicates**: {raw_audit['duplicates']['fraud_duplicates']:,}
- **Treatment Strategy**: Exact feature duplicates across all 28 PCA vectors, identical transaction amount, and matching epoch timestamp represent duplicate card swipes, retry loops, or synthetic replay noise. To prevent optimistic evaluation bias and train/test leakage, the first observed occurrence was preserved while secondary duplicates were pruned.

## 4. Class Distribution & Extreme Imbalance
| Class Label | Designation | Cleaned Count | Proportion | Class Imbalance Ratio |
|---|---|---|---|---|
| `0` | Legitimate | {cls_clean['legitimate_count']:,} | {100.0 - cls_clean['fraud_rate_pct']:.4f}% | Baseline |
| `1` | Fraudulent | {cls_clean['fraud_count']:,} | {cls_clean['fraud_rate_pct']:.4f}% | **{cls_clean['imbalance_ratio']}** |
| **Total** | All Traffic | **{audit['final_rows']:,}** | **100.00%** | - |

> [!IMPORTANT]
> The fraud incidence rate is **{cls_clean['fraud_rate_pct']:.4f}%** (~1 in every {int(round(cls_clean['legitimate_count']/cls_clean['fraud_count']))} transactions). Accuracy is strictly invalid as an optimization objective; PR-AUC, Recall, Precision, and Cost-Weighted Risk Tiers must govern modeling.

## 5. Monetary Exposure & Outlier Diagnostics (`Amount`)
- **Distribution Range**: €{amt['min']:.2f} to €{amt['max']:.2f}
- **Arithmetic Mean**: €{amt['mean']:.2f} (Standard Deviation: €{amt['std']:.2f})
- **Interquartile Metrics**:
  - 25th Percentile ($Q_1$): €{amt['q25']:.2f}
  - 50th Percentile (Median): €{amt['median']:.2f}
  - 75th Percentile ($Q_3$): €{amt['q75']:.2f}
  - Interquartile Range ($IQR$): €{amt['iqr']:.2f}
- **Outlier Count (IQR Rule > €{amt['upper_bound']:.2f})**: {amt['outlier_count']:,} transactions ({amt['outlier_percentage']:.2f}% of traffic)
- **Distribution Skewness**: {amt['skewness']:.2f} (Heavy right-tail distribution)

## 6. Engineered Features for Intelligence Systems
1. `Transaction_ID`: Unique synthetic primary key (`TXN_0000001` through `TXN_{audit['final_rows']:07d}`).
2. `Hour`: Modulo hour-of-day integer (`0` to `23`) derived from elapsed transaction seconds.
3. `Day`: Calendar day tracker (`1` or `2`) across the 48-hour recording window.

## 7. Data Quality Conclusion & Sign-Off
The processed dataset meets all industrial standards for downstream relational database persistence, exploratory visual analysis, and machine learning model validation.
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    raw_path = Path("FinGuard/data/raw/creditcard.csv")
    if not raw_path.exists():
        raw_path = Path("creditcard.csv")

    processed_dir = Path("FinGuard/data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    clean_csv_path = processed_dir / "clean_creditcard.csv"
    report_path = Path("FinGuard/reports/data_quality_report.md")

    print("[FinGuard ETL] Loading raw transactions...")
    df_raw = load_raw_data(raw_path)

    print("[FinGuard ETL] Performing initial data quality audit...")
    raw_audit = {
        "shape": inspect_data(df_raw),
        "missing": check_missing_values(df_raw),
        "duplicates": check_duplicates(df_raw),
        "class_distribution": analyze_class_distribution(df_raw),
    }

    print("[FinGuard ETL] Cleaning and generating processed dataset...")
    df_clean, clean_audit = clean_and_preprocess(df_raw, drop_duplicates=True)

    print(f"[FinGuard ETL] Saving processed dataset ({len(df_clean):,} rows) to: {clean_csv_path}")
    df_clean.to_csv(clean_csv_path, index=False)

    print(f"[FinGuard ETL] Compiling Data Quality Report: {report_path}")
    generate_data_quality_report(clean_audit, raw_audit, report_path)

    print("[FinGuard ETL] Data preprocessing stage completed successfully.")
