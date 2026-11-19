"""
Unit and Integration Tests for FinGuard Data Cleaning & Preprocessing.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Ensure FinGuard is in python path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_cleaning import (
    load_raw_data,
    inspect_data,
    check_missing_values,
    check_duplicates,
    analyze_class_distribution,
    analyze_outliers,
    clean_and_preprocess,
)


@pytest.fixture
def sample_transaction_df():
    """Generates synthetic transactions mimicking creditcard.csv schema."""
    np.random.seed(42)
    n = 100
    data = {
        "Time": np.sort(np.random.uniform(0, 172800, size=n)),
        "Amount": np.random.exponential(scale=50, size=n),
        "Class": np.random.choice([0, 1], size=n, p=[0.95, 0.05]),
    }
    for i in range(1, 29):
        data[f"V{i}"] = np.random.normal(loc=0, scale=1.0, size=n)

    df = pd.DataFrame(data)
    # Add an explicit duplicate row
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    return df


def test_inspect_data_structure(sample_transaction_df):
    meta = inspect_data(sample_transaction_df)
    assert meta["num_rows"] == 101
    assert meta["num_columns"] == 31
    assert "Time" in meta["columns"]
    assert "Amount" in meta["columns"]
    assert "Class" in meta["columns"]
    assert meta["memory_mb"] > 0


def test_check_missing_values(sample_transaction_df):
    summary = check_missing_values(sample_transaction_df)
    assert len(summary) == 31
    assert summary["Missing_Count"].sum() == 0


def test_check_missing_values_with_nulls():
    df = pd.DataFrame({
        "Time": [0, 1, np.nan],
        "Amount": [10.0, np.nan, 30.0],
        "Class": [0, 0, 1],
    })
    summary = check_missing_values(df)
    time_row = summary[summary["Feature"] == "Time"].iloc[0]
    assert time_row["Missing_Count"] == 1


def test_check_duplicates_detection(sample_transaction_df):
    res = check_duplicates(sample_transaction_df)
    assert res["duplicate_count"] == 1
    assert res["duplicate_percentage"] > 0


def test_analyze_class_distribution(sample_transaction_df):
    dist = analyze_class_distribution(sample_transaction_df)
    assert dist["total_transactions"] == 101
    assert dist["legitimate_count"] + dist["fraud_count"] == 101
    assert dist["fraud_rate_pct"] >= 0


def test_analyze_outliers_iqr(sample_transaction_df):
    outliers = analyze_outliers(sample_transaction_df, column="Amount")
    assert outliers["feature"] == "Amount"
    assert outliers["min"] >= 0
    assert outliers["max"] >= outliers["min"]
    assert outliers["upper_bound"] >= outliers["median"]


def test_clean_and_preprocess_pipeline(sample_transaction_df):
    clean_df, audit = clean_and_preprocess(sample_transaction_df, drop_duplicates=True)
    # 1 duplicate dropped
    assert clean_df.shape[0] == 100
    assert "Transaction_ID" in clean_df.columns
    assert "Hour" in clean_df.columns
    assert "Day" in clean_df.columns
    assert clean_df["Hour"].min() >= 0
    assert clean_df["Hour"].max() <= 23
    assert clean_df["Day"].min() >= 1
    assert clean_df["Day"].max() <= 3
    assert clean_df["Transaction_ID"].iloc[0] == "TXN_0000001"
    assert audit["dropped_duplicates"] == 1


def test_load_raw_data_raises_on_missing_file():
    with pytest.raises(FileNotFoundError):
        load_raw_data("non_existent_directory/missing.csv")
