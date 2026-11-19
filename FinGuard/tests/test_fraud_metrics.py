"""
Unit and Integration Tests for FinGuard SQL Analytics and Metric Parity.
"""

import sqlite3
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database import get_connection, run_query, parse_sql_file


@pytest.fixture
def test_db(tmp_path):
    """Creates a temporary in-memory or file-backed SQLite database with sample transactions."""
    db_file = tmp_path / "test_finguard.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE transactions (
            Transaction_ID TEXT PRIMARY KEY,
            Time REAL NOT NULL,
            Day INTEGER NOT NULL,
            Hour INTEGER NOT NULL,
            Amount REAL NOT NULL,
            V1 REAL, V2 REAL, V3 REAL, V4 REAL, V5 REAL, V6 REAL, V7 REAL, V8 REAL,
            V9 REAL, V10 REAL, V11 REAL, V12 REAL, V13 REAL, V14 REAL, V15 REAL,
            V16 REAL, V17 REAL, V18 REAL, V19 REAL, V20 REAL, V21 REAL, V22 REAL,
            V23 REAL, V24 REAL, V25 REAL, V26 REAL, V27 REAL, V28 REAL,
            Class INTEGER NOT NULL CHECK(Class IN (0, 1))
        );
    """)
    # Insert 10 synthetic rows: 8 legit, 2 fraud
    sample_data = [
        ("TXN_0000001", 100.0, 1, 2, 50.0, 0),
        ("TXN_0000002", 200.0, 1, 2, 120.0, 1),
        ("TXN_0000003", 300.0, 1, 5, 20.0, 0),
        ("TXN_0000004", 400.0, 1, 10, 1500.0, 0),
        ("TXN_0000005", 500.0, 1, 14, 300.0, 1),
        ("TXN_0000006", 600.0, 2, 8, 45.0, 0),
        ("TXN_0000007", 700.0, 2, 12, 15.0, 0),
        ("TXN_0000008", 800.0, 2, 18, 250.0, 0),
        ("TXN_0000009", 900.0, 2, 21, 80.0, 0),
        ("TXN_0000010", 1000.0, 2, 23, 10.0, 0),
    ]
    cur.executemany(
        """INSERT INTO transactions (Transaction_ID, Time, Day, Hour, Amount, Class)
           VALUES (?, ?, ?, ?, ?, ?);""",
        sample_data,
    )
    conn.commit()
    conn.close()
    return db_file


def test_database_connection(test_db):
    conn = get_connection(test_db)
    assert conn is not None
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM transactions;")
    count = cur.fetchone()[0]
    conn.close()
    assert count == 10


def test_q1_total_transactions(test_db):
    df = run_query(test_db, "SELECT COUNT(*) AS total_transactions FROM transactions;")
    assert df.iloc[0]["total_transactions"] == 10


def test_q2_q3_class_split(test_db):
    df_fraud = run_query(test_db, "SELECT COUNT(*) AS fraud FROM transactions WHERE Class = 1;")
    df_legit = run_query(test_db, "SELECT COUNT(*) AS legit FROM transactions WHERE Class = 0;")
    assert df_fraud.iloc[0]["fraud"] == 2
    assert df_legit.iloc[0]["legit"] == 8


def test_q4_fraud_percentage(test_db):
    sql = """
    SELECT 
        COUNT(*) AS total,
        SUM(Class) AS fraud,
        ROUND((CAST(SUM(Class) AS REAL) / COUNT(*)) * 100.0, 2) AS fraud_pct
    FROM transactions;
    """
    df = run_query(test_db, sql)
    assert df.iloc[0]["total"] == 10
    assert df.iloc[0]["fraud"] == 2
    assert df.iloc[0]["fraud_pct"] == 20.0


def test_q5_average_amount_split(test_db):
    sql = """
    SELECT 
        ROUND(AVG(CASE WHEN Class = 0 THEN Amount END), 2) AS avg_legit,
        ROUND(AVG(CASE WHEN Class = 1 THEN Amount END), 2) AS avg_fraud
    FROM transactions;
    """
    df = run_query(test_db, sql)
    # Legit: 50 + 20 + 1500 + 45 + 15 + 250 + 80 + 10 = 1970 / 8 = 246.25
    # Fraud: 120 + 300 = 420 / 2 = 210.0
    assert df.iloc[0]["avg_legit"] == 246.25
    assert df.iloc[0]["avg_fraud"] == 210.0


def test_parse_sql_queries_file():
    queries_file = ROOT / "sql" / "fraud_analysis_queries.sql"
    parsed = parse_sql_file(queries_file)
    assert len(parsed) == 15
    for q_num, title, sql in parsed:
        assert len(q_num) > 0
        assert len(title) > 0
        assert "SELECT" in sql.upper()


def test_prepare_features_and_target():
    from src.fraud_detection import prepare_features_and_target
    df = pd.DataFrame({
        "Transaction_ID": ["TXN_1", "TXN_2"],
        "Amount": [10.0, 20.0],
        "Time": [1.0, 2.0],
        "V1": [0.1, -0.1],
        "Class": [0, 1],
    })
    X, y, cols = prepare_features_and_target(df)
    assert "Transaction_ID" not in X.columns
    assert "Class" not in X.columns
    assert list(y) == [0, 1]
    assert "Amount" in cols
    assert "V1" in cols


def test_create_train_test_split_stratification():
    from src.fraud_detection import create_train_test_split
    X = pd.DataFrame({"feat": range(100)})
    y = pd.Series([0] * 90 + [1] * 10)
    X_train, X_test, y_train, y_test = create_train_test_split(X, y, test_size=0.20, random_state=42)
    assert len(X_train) == 80
    assert len(X_test) == 20
    # Stratified: exactly 2 fraud (10%) in test set
    assert y_test.sum() == 2
    assert y_train.sum() == 8


def test_serialized_model_artifact():
    import joblib
    model_path = ROOT / "data" / "processed" / "best_model.joblib"
    if model_path.exists():
        artifact = joblib.load(model_path)
        assert "model" in artifact
        assert "scaler" in artifact
        assert "optimal_threshold" in artifact
        assert 0.0 < artifact["optimal_threshold"] < 1.0


def test_calculate_risk_score_bounds_and_monotonicity():
    from src.risk_scoring import calculate_risk_score
    probs = np.array([0.0, 0.02, 0.05, 0.10, 0.20, 0.50, 1.0])
    scores = calculate_risk_score(probs)
    assert len(scores) == len(probs)
    assert np.all(scores >= 0.0)
    assert np.all(scores <= 100.0)
    # Check monotonicity
    assert np.all(np.diff(scores) >= 0.0)
    # Operational mapping: prob >= 0.20 must map to >= 75.0
    assert scores[4] >= 75.0


def test_assign_risk_tiers():
    from src.risk_scoring import assign_risk_tiers
    scores = np.array([10.0, 39.9, 40.0, 74.9, 75.0, 99.0])
    categories, statuses = assign_risk_tiers(scores)
    assert categories[0] == "Low Risk"
    assert categories[1] == "Low Risk"
    assert categories[2] == "Medium Risk"
    assert categories[3] == "Medium Risk"
    assert categories[4] == "High Risk"
    assert categories[5] == "High Risk"
    assert "Pending Triage" in statuses[4]


def test_investigation_priority_queue_file():
    queue_file = ROOT / "data" / "processed" / "investigation_priority_queue.csv"
    if queue_file.exists():
        df_queue = pd.read_csv(queue_file)
        assert "Transaction_ID" in df_queue.columns
        assert "Amount" in df_queue.columns
        assert "Fraud_Risk_Score" in df_queue.columns
        assert "Risk_Category" in df_queue.columns
        assert "Investigation_Status" in df_queue.columns
        assert (df_queue["Fraud_Risk_Score"] >= 75.0).all()



