"""
FinGuard - Banking Fraud Detection & Transaction Intelligence System
File: main.py
Purpose: Master CLI Orchestrator providing an end-to-end interface to execute all
         data engineering, analytics, modeling, risk scoring, and testing pipelines.
"""

from __future__ import annotations
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_cleaning import clean_and_preprocess, generate_data_quality_report, inspect_data, check_missing_values, check_duplicates, analyze_class_distribution, load_raw_data
from src.exploratory_analysis import run_full_eda
from src.database import init_database, populate_transactions, execute_all_analysis_queries
from src.fraud_detection import run_model_pipeline
from src.risk_scoring import run_risk_scoring_pipeline
from src.generate_powerbi_feeds import generate_feeds


def run_clean_step() -> None:
    print("\n" + "=" * 70)
    print("STEP 1: DATA CLEANING & PREPROCESSING")
    print("=" * 70)
    raw_path = PROJECT_ROOT / "data" / "raw" / "creditcard.csv"
    if not raw_path.exists():
        raw_path = PROJECT_ROOT.parent / "creditcard.csv"
    
    clean_path = PROJECT_ROOT / "data" / "processed" / "clean_creditcard.csv"
    report_path = PROJECT_ROOT / "reports" / "data_quality_report.md"

    print(f"Loading raw data from: {raw_path}")
    df_raw = load_raw_data(raw_path)
    raw_audit = {
        "shape": inspect_data(df_raw),
        "missing": check_missing_values(df_raw),
        "duplicates": check_duplicates(df_raw),
        "class_distribution": analyze_class_distribution(df_raw),
    }
    df_clean, clean_audit = clean_and_preprocess(df_raw, drop_duplicates=True)
    df_clean.to_csv(clean_path, index=False)
    generate_data_quality_report(clean_audit, raw_audit, report_path)
    print(f"[Done] Cleaned {len(df_clean):,} records saved to: {clean_path}")


def run_eda_step() -> None:
    print("\n" + "=" * 70)
    print("STEP 2: EXPLORATORY DATA ANALYSIS (EDA)")
    print("=" * 70)
    clean_path = PROJECT_ROOT / "data" / "processed" / "clean_creditcard.csv"
    fig_dir = PROJECT_ROOT / "reports" / "figures"
    results = run_full_eda(clean_path, fig_dir)
    print(f"[Done] Generated {len(results['figures'])} figures in: {fig_dir}")


def run_sql_step() -> None:
    print("\n" + "=" * 70)
    print("STEP 3: SQL DATABASE & 15 ANALYTICAL QUERIES")
    print("=" * 70)
    db_file = PROJECT_ROOT / "data" / "finguard.db"
    schema_file = PROJECT_ROOT / "sql" / "schema.sql"
    clean_csv = PROJECT_ROOT / "data" / "processed" / "clean_creditcard.csv"
    queries_file = PROJECT_ROOT / "sql" / "fraud_analysis_queries.sql"

    init_database(db_file, schema_file)
    populate_transactions(db_file, clean_csv)
    results = execute_all_analysis_queries(db_file, queries_file)
    print(f"[Done] Executed all {len(results)} queries against {db_file.name}")


def run_train_step() -> None:
    print("\n" + "=" * 70)
    print("STEP 4: MACHINE LEARNING MODEL TRAINING & BENCHMARK")
    print("=" * 70)
    clean_csv = PROJECT_ROOT / "data" / "processed" / "clean_creditcard.csv"
    model_file = PROJECT_ROOT / "data" / "processed" / "best_model.joblib"
    report_file = PROJECT_ROOT / "reports" / "model_evaluation.md"

    res = run_model_pipeline(clean_csv, model_file, report_file)
    print(f"[Done] Best model ({res['best_model_name']}) serialized to: {model_file.name}")


def run_score_step() -> None:
    print("\n" + "=" * 70)
    print("STEP 5: FRAUD RISK SCORING & INVESTIGATION QUEUE")
    print("=" * 70)
    clean_csv = PROJECT_ROOT / "data" / "processed" / "clean_creditcard.csv"
    model_file = PROJECT_ROOT / "data" / "processed" / "best_model.joblib"
    scored_csv = PROJECT_ROOT / "data" / "processed" / "scored_transactions.csv"
    queue_csv = PROJECT_ROOT / "data" / "processed" / "investigation_priority_queue.csv"

    res = run_risk_scoring_pipeline(clean_csv, model_file, scored_csv, queue_csv)
    print(f"[Done] Scored {res['total_scored']:,} transactions. High-risk queue: {res['high_risk_count']:,} tickets.")


def run_powerbi_step() -> None:
    print("\n" + "=" * 70)
    print("STEP 6: POWER BI DATA FEEDS EXPORT")
    print("=" * 70)
    scored_csv = PROJECT_ROOT / "data" / "processed" / "scored_transactions.csv"
    out_dir = PROJECT_ROOT / "powerbi" / "data"
    generate_feeds(scored_csv, out_dir)
    print(f"[Done] Power BI feeds exported to: {out_dir}")


def run_tests_step() -> None:
    print("\n" + "=" * 70)
    print("STEP 7: RUNNING AUTOMATED TEST SUITE")
    print("=" * 70)
    cmd = [sys.executable, "-m", "pytest", str(PROJECT_ROOT / "tests"), "-v"]
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="FinGuard: Banking Fraud Detection & Transaction Intelligence CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--all", action="store_true", help="Execute complete end-to-end pipeline")
    parser.add_argument("--clean", action="store_true", help="Run data cleaning and preprocessing")
    parser.add_argument("--eda", action="store_true", help="Run exploratory analysis and generate charts")
    parser.add_argument("--sql", action="store_true", help="Initialize database and execute 15 SQL queries")
    parser.add_argument("--train", action="store_true", help="Train and evaluate fraud classification models")
    parser.add_argument("--score", action="store_true", help="Generate 3-tier risk scores and priority queue")
    parser.add_argument("--powerbi", action="store_true", help="Export Power BI aggregated datasets")
    parser.add_argument("--test", action="store_true", help="Run automated test suite (pytest)")

    args = parser.parse_args()

    # If no flags passed, display menu or run --all
    if not any(vars(args).values()):
        print("\nFinGuard Master Pipeline CLI")
        print("Usage examples:")
        print("  python main.py --all       # Run entire pipeline end-to-end")
        print("  python main.py --sql       # Run SQLite database & 15 queries")
        print("  python main.py --score     # Run risk scoring engine")
        print("  python main.py --test      # Run automated tests\n")
        parser.print_help()
        sys.exit(0)

    t_start = time.time()

    if args.all or args.clean:
        run_clean_step()

    if args.all or args.eda:
        run_eda_step()

    if args.all or args.sql:
        run_sql_step()

    if args.all or args.train:
        run_train_step()

    if args.all or args.score:
        run_score_step()

    if args.all or args.powerbi:
        run_powerbi_step()

    if args.all or args.test:
        run_tests_step()

    total_time = time.time() - t_start
    print(f"\n{'='*70}\n[FinGuard] Pipeline execution completed successfully in {total_time:.2f}s.\n{'='*70}")


if __name__ == "__main__":
    main()

