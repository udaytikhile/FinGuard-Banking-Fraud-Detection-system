# FinGuard – Enterprise Power BI Dashboard Specification

## 0. Quick Start: Interactive Power BI Report
The fully developed, interactive dashboard report is saved directly in this folder:
- **Report File**: `Bank Fraud Transaction.pbix` (127.3 MB) — *Stored locally due to GitHub's 100MB limit*
- **Instructions**: Double-click `Bank Fraud Transaction.pbix` to open it in **Power BI Desktop**. It includes all pre-configured visuals, Star Schema relationships, DAX measures, interactive slicers, and the enterprise Dark Navy theme.

---

## 1. Overview & Architecture
The **FinGuard Power BI Intelligence Suite** provides interactive visual monitoring for financial fraud investigators, risk executives, and compliance officers. The reporting suite is structured into 3 purpose-built analytical pages adhering to the FinGuard Dark Navy enterprise design standard.

```
FinGuard Power BI Suite
├── Report File
│   └── Bank Fraud Transaction.pbix       # Interactive 3-page Power BI dashboard
├── Data Feeds (/powerbi/data/)
│   ├── page1_executive_kpis.csv          # Executive KPI cards feed
│   ├── hourly_volume_and_fraud.csv       # 24-hour diurnal and velocity trends
│   ├── amount_tier_distribution.csv      # 5 monetary exposure brackets
│   ├── risk_intelligence_summary.csv     # 3-tier portfolio breakdown
│   └── investigation_queue_feed.csv      # High-risk analyst ticket queue
├── Theme
│   └── FinGuard_Theme.json               # Enterprise dark navy theme palette
├── DAX Measures
│   └── dax_measures.dax                  # Formatted DAX calculations
└── Implementation Guide
    └── README.md                         # This implementation specification
```

---

## 2. Design & Visual Theme Settings
- **Canvas Background**: Deep Navy (`#0A192F`)
- **Visual Container Cards**: Slate Blue (`#172A45`) with subtle border (`#233554`) and drop shadows
- **KPI Accent**: Cyan Teal (`#00E5FF`)
- **Alert / Fraud Markers**: Crimson Coral (`#FF4D4D`)
- **Caution / Threshold**: Warning Amber (`#FFAA00`)
- **Typography**: Header `Segoe UI Semibold`, Body `Segoe UI`, Numbers `Consolas` / `Segoe UI Mono`

To apply the theme:
1. In Power BI Desktop, navigate to **View > Themes > Browse for themes...**
2. Select `powerbi/FinGuard_Theme.json`.

---

## 3. Data Model & Relationships (Star Schema)

### Tables
1. **Fact_Transactions** (`scored_transactions.csv` or `investigation_queue_feed.csv`):
   - Primary Key: `Transaction_ID`
   - Attributes: `Time`, `Day`, `Hour`, `Amount`, `Fraud_Probability`, `Fraud_Risk_Score`, `Risk_Category`, `Investigation_Status`, `Class`
2. **Dim_Hour** (`hourly_volume_and_fraud.csv`):
   - Key: `Hour` (0 to 23)
3. **Dim_AmountTier** (`amount_tier_distribution.csv`):
   - Key: `Amount_Bracket`
4. **Dim_RiskTier** (`risk_intelligence_summary.csv`):
   - Key: `Risk_Category`

---

## 4. Dashboard Page 1: Executive Overview

### Layout Configuration
- **Top Header Bar**: System Title (*FinGuard Fraud Intelligence Command Center*), System Status (*Live - 283,726 Transactions Loaded*), Date/Time Slicer (*Day 1, Day 2*).
- **Executive KPI Cards (Top Row, 6 Cards)**:
  1. **Total Transactions**: `283,726` (Measure: `[Total Transactions]`)
  2. **Fraud Transactions**: `473` (Measure: `[Fraud Transactions]`, Color: `#FF4D4D`)
  3. **Legitimate Transactions**: `283,253` (Measure: `[Legitimate Transactions]`, Color: `#00E5FF`)
  4. **Fraud Rate**: `0.1667%` (Measure: `[Fraud Rate %]`)
  5. **Total Turnover**: `€25,102,001.68` (Measure: `[Total Volume EUR]`)
  6. **Fraud Exposure**: `€58,591.39` (Measure: `[Fraud Exposure EUR]`, Share: `0.2334%`)

### Core Visualizations
1. **Fraud vs Legitimate Volume (100% Stacked Bar Chart)**:
   - Axis: Category (`Legitimate` vs `Fraudulent`)
   - Values: `[Total Transactions]`
   - Visual: 99.83% Legitimate vs 0.17% Fraudulent highlighting operational scale.
2. **Transaction Volume Trend (Area Chart)**:
   - X-Axis: `Hour` (0 to 23)
   - Y-Axis: `[Total Transactions]`
   - Visual: Diurnal business traffic cycle peaking between 10:00 and 21:00.
3. **Fraud Distribution by Day (Donut Chart)**:
   - Legend: `Day 1` vs `Day 2`
   - Values: `[Fraud Transactions]`
   - Metric: Day 1 (272 frauds, 57.5%) vs Day 2 (201 frauds, 42.5%).
4. **Transaction Amount Distribution (Clustered Column Chart)**:
   - X-Axis: `Amount_Bracket` (Under €25, €25-€99.99, €100-€299.99, €300-€999.99, €1,000+)
   - Y-Axis: `[Total Volume EUR]` (Column) and `[Fraud Exposure EUR]` (Line on secondary axis).

---

## 5. Dashboard Page 2: Fraud Analysis & Temporal Velocity

### Core Visualizations
1. ** Fraud by TransactionAmount Bracket (Horizontal Bar Chart)**:
   - Y-Axis: `Amount_Bracket`
   - X-Axis: `[Fraud Exposure EUR]`
   - Callout: Demonstrates that Bracket 4 (€300 - €999.99) accounts for **€27,396.98** (46.8% of total financial losses).
2. **Fraud Velocity by Hour of Day (Combination Line & Clustered Bar Chart)**:
   - X-Axis: `Hour` (0 to 23)
   - Column Values: `[Total Transactions]` (Traffic volume)
   - Line Values: `[Fraud Rate %]`
   - Callout: Clearly shows anomalous overnight fraud spikes at 02:00 (1.45% fraud rate) and 04:00 (1.04% fraud rate).
3. **Fraud Percentage Trend (Line Chart)**:
   - X-Axis: `Hour`
   - Legend: `Day 1` vs `Day 2`
   - Values: `[Fraud Rate %]`
4. **Fraud vs Legitimate Metric Comparison (Matrix Visual)**:
   - Rows: `Class Label` (Legitimate vs Fraudulent)
   - Values: Volume, Volume %, Total Turnover, Turnover %, Mean Ticket, Median Ticket, Max Ticket.

---

## 6. Dashboard Page 3: Risk Intelligence & Investigation Triage

### Executive Triage KPIs
1. **High-Risk Alerts**: `668` transactions (0.235% of traffic, 96.19% fraud capture rate).
2. **Medium-Risk Secondary Auth**: `2,016` transactions (0.711% of traffic).
3. **Low-Risk Auto-Cleared**: `281,042` transactions (99.054% of traffic).
4. **Capital Saved in High-Risk Queue**: `€54,808.60` (93.5% of total fraud exposure intercepted).

### Core Visualizations
1. **Risk Tier Stratification (Funnel Chart)**:
   - Stages: `Low Risk (Auto-Cleared)` -> `Medium Risk (Step-Up OTP)` -> `High Risk (Priority Triage)`
   - Values: `Total_Transactions`
2. **Risk Score Distribution (Histogram / Density Column Chart)**:
   - X-Axis: `Fraud_Risk_Score` (Binned into deciles: 0-10, 10-20, ..., 90-100)
   - Y-Axis: Transaction Count
   - Threshold Marker: Constant line at `Score = 75.0`.
3. **High-Risk Transaction Priority Queue (Interactive Table Visual)**:
   - Columns: `Transaction_ID`, `Day`, `Hour`, `Amount (€)`, `Fraud_Probability`, `Fraud_Risk_Score`, `Risk_Category`, `Investigation_Status`
   - Conditional Formatting:
     - `Fraud_Risk_Score`: Data bar with gradient from Amber (`#FFAA00`) to Crimson (`#FF4D4D`).
     - `Investigation_Status`: Font colored `#FF4D4D` for High Priority.
   - Slicers:
     - Minimum Risk Score Slider (`75.0` to `100.0`).
     - Amount Filter (`> €500`, `> €1,000`).
     - Day Slicer (`Day 1`, `Day 2`).

---

## 7. Interactive Slicers & Cross-Filtering Behavior
- **Global Filters**: Top rail filter on `Day` and `Amount Bracket` dynamically updates all 3 pages.
- **Cross-Filtering**: Clicking any hour in the *Hourly Fraud Velocity* chart cross-filters the *High-Risk Table* to display only transactions originating during that specific hour.

