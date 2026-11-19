"""
FinGuard - Banking Fraud Detection & Transaction Intelligence System
Module: database.py
Purpose: Manages SQLite database creation, indexed schema deployment, high-throughput
         batched ingestion of cleaned transactions, and analytical query execution.
"""

from __future__ import annotations
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Creates a configured connection to the SQLite analytical store."""
    conn = sqlite3.connect(str(db_path))
    # Pragmas for fast analytical reads and reliable transactions
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -64000;")  # 64MB cache
    return conn


def init_database(db_path: str | Path, schema_path: str | Path) -> None:
    """Executes the DDL schema to establish table structures and composite indices."""
    db_file = Path(db_path)
    schema_file = Path(schema_path)

    if not schema_file.is_file():
        raise FileNotFoundError(f"Schema file not found at: {schema_file.resolve()}")

    db_file.parent.mkdir(parents=True, exist_ok=True)
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_connection(db_file) as conn:
        conn.executescript(schema_sql)
        conn.commit()


def populate_transactions(
    db_path: str | Path,
    csv_path: str | Path,
    batch_size: int = 25000,
) -> int:
    """
    Ingests cleaned transactions from CSV into SQLite table in chunked batches.
    Returns total number of rows inserted.
    """
    csv_file = Path(csv_path)
    if not csv_file.is_file():
        raise FileNotFoundError(f"Cleaned CSV dataset not found at: {csv_file.resolve()}")

    total_inserted = 0
    t0 = time.time()

    with get_connection(db_path) as conn:
        # Check if table already populated
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM transactions;")
        existing_count = cur.fetchone()[0]
        if existing_count > 0:
            print(f"[FinGuard DB] Table already contains {existing_count:,} records. Ingestion skipped.")
            return existing_count

        print(f"[FinGuard DB] Ingesting {csv_file.name} in chunks of {batch_size:,}...")
        for chunk in pd.read_csv(csv_file, chunksize=batch_size):
            chunk.to_sql("transactions", conn, if_exists="append", index=False)
            total_inserted += len(chunk)
            print(f"[FinGuard DB] Inserted {total_inserted:,} rows...", flush=True)

        conn.commit()

    duration = time.time() - t0
    print(f"[FinGuard DB] Ingestion complete: {total_inserted:,} records loaded in {duration:.2f}s.")
    return total_inserted


def run_query(db_path: str | Path, query: str, params: Optional[Tuple[Any, ...]] = None) -> pd.DataFrame:
    """Executes an SQL query against the database and returns a pandas DataFrame."""
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df


def parse_sql_file(queries_path: str | Path) -> List[Tuple[str, str, str]]:
    """
    Parses fraud_analysis_queries.sql into distinct query blocks.
    Returns list of (query_number, query_title, sql_text).
    """
    path = Path(queries_path)
    if not path.is_file():
        raise FileNotFoundError(f"SQL queries file not found: {path.resolve()}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by QUERY header comments
    pattern = re.compile(
        r"-- QUERY\s+(\d+):\s+([^\n]+).*?(-- Q\d+:[^\n]*\n)(SELECT.*?;)",
        re.DOTALL | re.IGNORECASE,
    )
    matches = pattern.findall(content)
    
    parsed = []
    for q_num, title, _, sql in matches:
        parsed.append((q_num.strip(), title.strip(), sql.strip()))

    # Fallback if regex missed any format variations
    if len(parsed) < 15:
        # Simple semicolon split
        raw_statements = [s.strip() for s in content.split(";") if "SELECT" in s.upper()]
        parsed = []
        for idx, stmt in enumerate(raw_statements, start=1):
            parsed.append((str(idx), f"Query {idx}", stmt + ";"))

    return parsed[:15]


def execute_all_analysis_queries(
    db_path: str | Path,
    queries_path: str | Path,
) -> Dict[str, pd.DataFrame]:
    """
    Executes all 15 analytical SQL queries, prints formatted results,
    and returns a dictionary mapping query labels to result DataFrames.
    """
    queries = parse_sql_file(queries_path)
    results = {}

    print(f"\n{'='*75}")
    print(f"FinGuard Analytical SQL Query Execution Engine (Total Queries: {len(queries)})")
    print(f"{'='*75}\n")

    for q_num, title, sql in queries:
        label = f"Q{q_num}: {title}"
        df_res = run_query(db_path, sql)
        results[f"Q{q_num}"] = df_res

        print(f"[{label}]")
        print(df_res.to_string(index=False))
        print("-" * 75)

    return results


if __name__ == "__main__":
    db_file = Path("FinGuard/data/finguard.db")
    schema_file = Path("FinGuard/sql/schema.sql")
    clean_csv = Path("FinGuard/data/processed/clean_creditcard.csv")
    queries_file = Path("FinGuard/sql/fraud_analysis_queries.sql")

    print("[FinGuard DB] Initializing SQLite schema...")
    init_database(db_file, schema_file)

    print("[FinGuard DB] Ingesting cleaned transactions...")
    populate_transactions(db_file, clean_csv)

    print("[FinGuard DB] Running all 15 analytical queries...")
    results = execute_all_analysis_queries(db_file, queries_file)
    print(f"\n[FinGuard DB] All {len(results)} analytical queries executed successfully.")

