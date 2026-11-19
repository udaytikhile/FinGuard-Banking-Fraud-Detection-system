# FinGuard – Data Quality & Preprocessing Audit Report

## 1. Executive Summary
- **Audit Date**: 2026-11-05
- **Dataset Domain**: Credit Card Financial Transactions (48-hour European cardholder window)
- **Objective**: Establish baseline data integrity, validate schemas, resolve duplicate transactions, and produce an investigation-ready dataset for fraud detection and business intelligence.

## 2. Ingestion & Schema Verification
| Parameter | Raw Dataset | Cleaned Dataset |
|---|---|---|
| Total Rows | 284,807 | 283,726 |
| Total Features | 31 | 34 |
| In-Memory Size | 67.36 MB | 73.60 MB |
| Primary Key | None | `Transaction_ID` (Added) |
| Missing Values | 0 (0.00%) | 0 (0.00%) |
| Duplicate Transactions | 1,081 (0.380%) | 0 (Deduplicated) |

## 3. Duplicate Transaction Treatment
- **Total Identical Records Found**: 1,081
- **Legitimate Duplicates**: 1,062
- **Fraudulent Duplicates**: 19
- **Treatment Strategy**: Exact feature duplicates across all 28 PCA vectors, identical transaction amount, and matching epoch timestamp represent duplicate card swipes, retry loops, or synthetic replay noise. To prevent optimistic evaluation bias and train/test leakage, the first observed occurrence was preserved while secondary duplicates were pruned.

## 4. Class Distribution & Extreme Imbalance
| Class Label | Designation | Cleaned Count | Proportion | Class Imbalance Ratio |
|---|---|---|---|---|
| `0` | Legitimate | 283,253 | 99.8333% | Baseline |
| `1` | Fraudulent | 473 | 0.1667% | **1:599** |
| **Total** | All Traffic | **283,726** | **100.00%** | - |

> [!IMPORTANT]
> The fraud incidence rate is **0.1667%** (~1 in every 599 transactions). Accuracy is strictly invalid as an optimization objective; PR-AUC, Recall, Precision, and Cost-Weighted Risk Tiers must govern modeling.

## 5. Monetary Exposure & Outlier Diagnostics (`Amount`)
- **Distribution Range**: €0.00 to €25691.16
- **Arithmetic Mean**: €88.47 (Standard Deviation: €250.40)
- **Interquartile Metrics**:
  - 25th Percentile ($Q_1$): €5.60
  - 50th Percentile (Median): €22.00
  - 75th Percentile ($Q_3$): €77.51
  - Interquartile Range ($IQR$): €71.91
- **Outlier Count (IQR Rule > €185.38)**: 31,685 transactions (11.17% of traffic)
- **Distribution Skewness**: 16.98 (Heavy right-tail distribution)

## 6. Engineered Features for Intelligence Systems
1. `Transaction_ID`: Unique synthetic primary key (`TXN_0000001` through `TXN_0283726`).
2. `Hour`: Modulo hour-of-day integer (`0` to `23`) derived from elapsed transaction seconds.
3. `Day`: Calendar day tracker (`1` or `2`) across the 48-hour recording window.

## 7. Data Quality Conclusion & Sign-Off
The processed dataset meets all industrial standards for downstream relational database persistence, exploratory visual analysis, and machine learning model validation.
