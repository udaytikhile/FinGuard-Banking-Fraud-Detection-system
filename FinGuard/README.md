# Banking Fraud Detection & Transaction Intelligence

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)](https://scikit-learn.org/)
[![Database SQLite](https://img.shields.io/badge/SQL-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![Power BI](https://img.shields.io/badge/Power_BI-Report_Included-F2C811.svg)](powerbi/)
[![Tests Passing](https://img.shields.io/badge/Tests-20%2F20%20Passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Project Overview
An end-to-end data analytics and transaction intelligence project designed to detect suspicious banking transactions, uncover financial crime patterns, and optimize fraud investigation operations under extreme class imbalance.

FinGuard audits credit card transaction streams, persists indexed records into an analytical SQLite store, performs statistical EDA, trains threshold-calibrated machine learning models, dynamically computes a 3-tier fraud risk score (0–100), and outputs priority investigation queues alongside an interactive Power BI dashboard (`Bank Fraud Transaction.pbix`).

---

## Objectives
- **Analyze banking transaction data**: Survey 284,807 credit card transactions across 48 hours.
- **Identify suspicious transaction patterns**: Isolate diurnal velocity anomalies and high-exposure clusters.
- **Clean and transform transaction records**: Remove duplicates, validate schemas, and engineer temporal features.
- **Perform exploratory data analysis**: Quantify class distributions, monetary turnover exposure, and feature separability.
- **Analyze fraud trends using SQL**: Ingest records into an analytical SQLite database and execute 15 business intelligence queries.
- **Build an interactive Power BI dashboard**: Provide executive KPI monitoring, fraud velocity trends, and analyst ticket queues via [`Bank Fraud Transaction.pbix`](powerbi/Bank%20Fraud%20Transaction.pbix).

---

## Technologies Used
- **Python**: Core programming language (3.11+, validated on 3.14.7)
- **Pandas & NumPy**: Data engineering, deduplication, and vectorized scoring
- **SQL / SQLite**: Relational data warehousing, indexing, and 15 analytical queries
- **Power BI**: Interactive 3-page dashboard ([`Bank Fraud Transaction.pbix`](powerbi/Bank%20Fraud%20Transaction.pbix)), DAX KPI measures, Star Schema
- **Scikit-Learn**: Machine learning classification (Random Forest, Logistic Regression, Isolation Forest, PR-AUC tuning)
- **Matplotlib & Seaborn**: Statistical charting and 6 publication-ready figures
- **Pytest**: Quality assurance test suite (20 automated unit and integration tests)

---

## Project Structure
```
FinGuard/
├── data/
│   ├── raw/
│   │   └── creditcard.csv                # 143.84 MB - Raw transactions (Single Source of Truth)
│   ├── processed/
│   │   ├── clean_creditcard.csv          # 148.25 MB - Deduplicated & preprocessed data
│   │   ├── scored_transactions.csv       # 159.62 MB - Model-scored & risk-tiered transactions
│   │   ├── investigation_priority_queue.csv # 50 KB - Top 500 analyst investigation tickets
│   │   └── best_model.joblib             # 2.92 MB - Serialized Random Forest model artifact
│   └── finguard.db                       # 101.36 MB - SQLite relational database store
├── notebooks/
│   ├── 01_data_exploration.ipynb         # Statistical EDA & distributions
│   ├── 02_data_cleaning.ipynb            # Deduplication, audit & schema validation
│   ├── 03_fraud_analysis.ipynb           # Temporal velocity & feature separability
│   └── 04_machine_learning.ipynb         # Model training & threshold tuning
├── src/
│   ├── data_cleaning.py                  # Deduplication, audit & temporal feature engineering
│   ├── exploratory_analysis.py           # Statistical summary & plot generator
│   ├── database.py                       # SQLite schema, batch ingestion & 15 queries engine
│   ├── fraud_detection.py                # ML models, PR-AUC tuning & serialization
│   ├── generate_powerbi_feeds.py         # Power BI pre-aggregated CSV feeds exporter
│   └── risk_scoring.py                   # 0-100 Triage scoring & priority queue engine
├── sql/
│   ├── schema.sql                        # Table DDL, composite indexes & integrity checks
│   └── fraud_analysis_queries.sql        # 15 analytical business intelligence queries
├── powerbi/
│   ├── Bank Fraud Transaction.pbix       # 127.3 MB - Interactive 3-page Power BI dashboard report
│   ├── README.md                         # 3-Page Power BI implementation guide
│   ├── FinGuard_Theme.json               # Dark Navy enterprise theme JSON
│   ├── dax_measures.dax                  # 20+ Formatted DAX KPI measures
│   └── data/                             # Pre-aggregated CSV feeds for dashboard import
├── reports/
│   ├── business_insights.md              # Executive analysis & strategic recommendations
│   ├── data_quality_report.md            # Data quality, duplicate audit & schema report
│   ├── model_evaluation.md               # Model comparison, PR-AUC & confusion matrices
│   ├── project_cleanup_report.md         # Full file reorganization & redundancy audit report
│   └── figures/                          # 6 high-resolution 300 DPI visualizations
├── tests/
│   ├── test_data_cleaning.py             # 8 unit tests for data preprocessing
│   └── test_fraud_metrics.py             # 12 integration tests for SQL, models & triage
├── requirements.txt                      # Project dependency specification
├── .gitignore                            # Clean repository exclusions
└── main.py                               # Master CLI orchestrator
```

---

## Analysis Workflow
1. **Data Collection & Ingestion**: Validated 284,807 transactions across 31 features (`Time`, `Amount`, `V1`–`V28`, `Class`).
2. **Data Cleaning & Transformation**: Audited missing values (0 found), removed 1,081 duplicate transactions, and engineered diurnal temporal features (`Hour`, `Day`).
3. **Exploratory Data Analysis**: Quantified severe class imbalance (0.1667%), evaluated financial exposure, and isolated key predictive drivers (`V14`, `V17`, `V12`, `V10`).
4. **SQL Analysis**: Ingested clean data into indexed SQLite tables and executed 15 complex queries (window functions, diurnal aggregations, hourly velocity).
5. **Fraud Pattern Identification & ML Modeling**: Benchmarked Random Forest and Logistic Regression against PR-AUC; calibrated decision threshold at 0.20 to balance fraud recovery against investigator alert fatigue.
6. **Risk Scoring & Triage**: Standardized continuous 0–100 risk score and triaged portfolio into Low (<40), Medium (40–74.9), and High Risk ($\ge$75).
7. **Power BI Dashboard Development**: Built the 3-page interactive [`Bank Fraud Transaction.pbix`](powerbi/Bank%20Fraud%20Transaction.pbix) report with custom DAX measures and enterprise Dark Navy styling.
8. **Business Insights & Recommendations**: Formulated operational policies for auto-clearing legitimate traffic and routing high-risk tickets to human analysts.

---

## Key Findings

- **Extreme Class Imbalance**:
  - Total Clean Transactions: **283,726**
  - Legitimate Transactions: **283,253 (99.8333%)**
  - Fraudulent Transactions: **473 (0.1667%)** (~1 fraud per 600 transactions).
- **Monetary Turnover & Exposure**:
  - Total Portfolio Turnover: **€25,102,002.04**
  - Gross Fraud Exposure: **€58,591.55** (0.233% of turnover).
  - Average Fraud Ticket: **€123.87** vs Average Legitimate Ticket: **€88.41**.
- **Diurnal Fraud Velocity Patterns**:
  - Fraud activity surges dramatically between **02:00 and 04:00 AM**, reaching a peak fraud rate of **1.45%** (over 8× baseline) when legitimate transaction volume is at diurnal minimum.
  - Hour 11:00 AM exhibits a secondary fraud spike with 53 fraudulent events (€8,241 exposure).
- **Triage Performance & Capital Protection**:
  - **High Risk Tier (Score $\ge$ 75.0)**: Catches **96.19% of all fraud (455 / 473)** and intercepts **€54,808.60 (93.5%) in financial exposure** across only **668 tickets (0.235% of total traffic)** with **68.11% precision**.
  - **Medium Risk Tier (Score 40–74.9)**: Routes 2,016 transactions (0.71% of volume) containing 4 frauds (€1,176 exposure) to automated step-up OTP challenge.
  - **Low Risk Tier (Score < 40)**: Safely auto-clears **99.05% of traffic (281,042 transactions | €24.87M volume)** with zero customer friction.

---

## Power BI Dashboard

The Power BI report file is located at [`powerbi/Bank Fraud Transaction.pbix`](powerbi/Bank%20Fraud%20Transaction.pbix) (127.3 MB).

### Dashboard Pages
1. **Executive Overview**: Executive KPI summary cards (Total Volume, Fraud Loss, Exposure Rate), 48-hour volume timeline, fraud vs legitimate split.
2. **Fraud Analysis**: Diurnal hourly fraud velocity combo chart, 5-tier amount bracket distribution, and day-over-day trends.
3. **Risk Intelligence**: 3-tier risk funnel, continuous risk score distribution, and interactive high-priority investigation queue table with slicers.

*Theme specification, DAX measures, and import instructions are detailed in [powerbi/README.md](powerbi/README.md).*

---

## How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Execute via Master CLI Orchestrator
Run the complete pipeline from root or FinGuard directory:
```bash
python main.py --all
```
Or execute individual steps:
```bash
python main.py --clean     # Step 1: Clean and preprocess data
python main.py --eda       # Step 2: Statistical EDA & 6 figures
python main.py --sql       # Step 3: SQLite database & 15 queries
python main.py --train     # Step 4: Train & evaluate ML models
python main.py --score     # Step 5: 3-tier risk scoring engine
python main.py --powerbi   # Step 6: Export Power BI data feeds
python main.py --test      # Step 7: Run automated test suite
```

### 3. Run Automated Tests
```bash
pytest tests -v
```
*(All 20 unit and integration tests passing in ~3.4s).*

### 4. Interactive Jupyter Notebooks
Navigate to `notebooks/` and launch Jupyter:
```bash
jupyter lab notebooks/
```
1. `01_data_exploration.ipynb`
2. `02_data_cleaning.ipynb`
3. `03_fraud_analysis.ipynb`
4. `04_machine_learning.ipynb`

### 5. Open Power BI Report
Open `powerbi/Bank Fraud Transaction.pbix` in **Power BI Desktop**.

---

## Author
**Data Analyst & Machine Learning Portfolio Project (2026)**
