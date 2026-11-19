-- ============================================================================
-- FinGuard - Banking Fraud Detection & Transaction Intelligence System
-- Analytical SQL Queries (15 Business Intelligence Queries)
-- Database: SQLite (finguard.db)
-- Author: Senior SQL / Analytics Engineer
-- Purpose: In-depth financial investigation, fraud exposure auditing,
--          temporal pattern analysis, and risk tiering.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 1: Total Transactions
-- Business Objective: Determine total ingested transaction volume for baseline auditing.
-- ----------------------------------------------------------------------------
-- Q1: Total Transaction Volume
SELECT 
    COUNT(*) AS total_transactions
FROM transactions;


-- ----------------------------------------------------------------------------
-- QUERY 2: Total Fraudulent Transactions
-- Business Objective: Identify absolute count of confirmed fraudulent events.
-- ----------------------------------------------------------------------------
-- Q2: Fraud Transaction Volume
SELECT 
    COUNT(*) AS total_fraud_transactions
FROM transactions
WHERE Class = 1;


-- ----------------------------------------------------------------------------
-- QUERY 3: Total Legitimate Transactions
-- Business Objective: Identify absolute count of legitimate customer transactions.
-- ----------------------------------------------------------------------------
-- Q3: Legitimate Transaction Volume
SELECT 
    COUNT(*) AS total_legitimate_transactions
FROM transactions
WHERE Class = 0;


-- ----------------------------------------------------------------------------
-- QUERY 4: Global Fraud Rate Percentage
-- Business Objective: Calculate the baseline fraud incidence percentage across the portfolio.
-- ----------------------------------------------------------------------------
-- Q4: Fraud Percentage
SELECT 
    COUNT(*) AS total_transactions,
    SUM(Class) AS fraud_transactions,
    ROUND((CAST(SUM(Class) AS REAL) / COUNT(*)) * 100.0, 4) AS fraud_percentage
FROM transactions;


-- ----------------------------------------------------------------------------
-- QUERY 5: Average Transaction Amount (Overall, Legitimate, and Fraudulent)
-- Business Objective: Contrast ticket sizes between typical customer activity and fraud attempts.
-- ----------------------------------------------------------------------------
-- Q5: Average Transaction Amount Comparison
SELECT 
    ROUND(AVG(Amount), 2) AS overall_avg_amount,
    ROUND(AVG(CASE WHEN Class = 0 THEN Amount END), 2) AS legit_avg_amount,
    ROUND(AVG(CASE WHEN Class = 1 THEN Amount END), 2) AS fraud_avg_amount
FROM transactions;


-- ----------------------------------------------------------------------------
-- QUERY 6: Maximum Transaction Amount (Overall and by Class)
-- Business Objective: Assess maximum monetary exposure cap across both customer categories.
-- ----------------------------------------------------------------------------
-- Q6: Maximum Transaction Amount
SELECT 
    ROUND(MAX(Amount), 2) AS max_amount_overall,
    ROUND(MAX(CASE WHEN Class = 0 THEN Amount END), 2) AS max_amount_legit,
    ROUND(MAX(CASE WHEN Class = 1 THEN Amount END), 2) AS max_amount_fraud
FROM transactions;


-- ----------------------------------------------------------------------------
-- QUERY 7: Minimum Transaction Amount
-- Business Objective: Check for micro-transactions or zero-value authorization probes.
-- ----------------------------------------------------------------------------
-- Q7: Minimum Transaction Amount
SELECT 
    ROUND(MIN(Amount), 2) AS min_amount_overall,
    ROUND(MIN(CASE WHEN Class = 0 THEN Amount END), 2) AS min_amount_legit,
    ROUND(MIN(CASE WHEN Class = 1 THEN Amount END), 2) AS min_amount_fraud
FROM transactions;


-- ----------------------------------------------------------------------------
-- QUERY 8: Fraud Amount Analysis (Complete Statistical Profile)
-- Business Objective: Comprehensive statistical audit of fraudulent transaction amounts.
-- ----------------------------------------------------------------------------
-- Q8: Comprehensive Fraud Amount Distribution
SELECT 
    COUNT(*) AS fraud_count,
    ROUND(SUM(Amount), 2) AS total_fraud_exposure_eur,
    ROUND(AVG(Amount), 2) AS avg_fraud_amount_eur,
    ROUND(MIN(Amount), 2) AS min_fraud_amount_eur,
    ROUND(MAX(Amount), 2) AS max_fraud_amount_eur
FROM transactions
WHERE Class = 1;


-- ----------------------------------------------------------------------------
-- QUERY 9: Fraud vs Legitimate Transaction Comparison
-- Business Objective: Comprehensive executive breakdown comparing volume and financial turnover share.
-- ----------------------------------------------------------------------------
-- Q9: Side-by-Side Class Performance Matrix
SELECT 
    CASE WHEN Class = 1 THEN 'Fraudulent' ELSE 'Legitimate' END AS transaction_category,
    COUNT(*) AS transaction_volume,
    ROUND(SUM(Amount), 2) AS total_turnover_eur,
    ROUND(AVG(Amount), 2) AS avg_amount_eur,
    ROUND(MIN(Amount), 2) AS min_amount_eur,
    ROUND(MAX(Amount), 2) AS max_amount_eur,
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM transactions)), 4) AS volume_share_pct,
    ROUND((SUM(Amount) * 100.0 / (SELECT SUM(Amount) FROM transactions)), 4) AS turnover_share_pct
FROM transactions
GROUP BY Class;


-- ----------------------------------------------------------------------------
-- QUERY 10: Transaction Volume Analysis by Temporal Bands
-- Business Objective: Group transactions into daily time-of-day operational blocks.
-- ----------------------------------------------------------------------------
-- Q10: Day & Time-of-Day Operational Window Volume
SELECT 
    Day,
    CASE 
        WHEN Hour BETWEEN 0 AND 5 THEN '00:00 - 05:59 (Overnight)'
        WHEN Hour BETWEEN 6 AND 11 THEN '06:00 - 11:59 (Morning)'
        WHEN Hour BETWEEN 12 AND 17 THEN '12:00 - 17:59 (Afternoon)'
        ELSE '18:00 - 23:59 (Evening)'
    END AS time_window,
    COUNT(*) AS transaction_volume,
    ROUND(SUM(Amount), 2) AS total_amount_eur,
    SUM(Class) AS fraud_events
FROM transactions
GROUP BY Day, time_window
ORDER BY Day ASC, MIN(Hour) ASC;


-- ----------------------------------------------------------------------------
-- QUERY 11: Time-Based Transaction Analysis (Hourly Fraud Velocity)
-- Business Objective: Hourly breakdown (00:00 - 23:00) identifying high fraud incidence hours.
-- ----------------------------------------------------------------------------
-- Q11: Hourly Fraud Velocity & Incidence Rate
SELECT 
    Hour,
    COUNT(*) AS total_volume,
    SUM(Class) AS fraud_count,
    ROUND((CAST(SUM(Class) AS REAL) / COUNT(*)) * 100.0, 4) AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN Class = 1 THEN Amount ELSE 0 END), 2) AS fraud_exposure_eur
FROM transactions
GROUP BY Hour
ORDER BY Hour ASC;


-- ----------------------------------------------------------------------------
-- QUERY 12: High-Value Transaction Analysis
-- Business Objective: Evaluate transactions across monetary exposure tiers (> €1,000, €100-€999, < €100).
-- ----------------------------------------------------------------------------
-- Q12: High-Value Segment Risk Exposure
SELECT 
    CASE 
        WHEN Amount >= 1000.0 THEN 'High Value (>= €1,000)'
        WHEN Amount >= 100.0 THEN 'Medium Value (€100 - €999.99)'
        ELSE 'Micro/Low Value (< €100)'
    END AS value_segment,
    COUNT(*) AS total_transactions,
    SUM(Class) AS fraud_transactions,
    ROUND((CAST(SUM(Class) AS REAL) / COUNT(*)) * 100.0, 4) AS fraud_rate_pct,
    ROUND(SUM(Amount), 2) AS total_segment_volume_eur,
    ROUND(SUM(CASE WHEN Class = 1 THEN Amount ELSE 0 END), 2) AS segment_fraud_exposure_eur
FROM transactions
GROUP BY value_segment
ORDER BY MIN(Amount) DESC;


-- ----------------------------------------------------------------------------
-- QUERY 13: Daily Fraud Trends (Day 1 vs Day 2)
-- Business Objective: Compare day-over-day fraud volume, rate, and financial loss.
-- ----------------------------------------------------------------------------
-- Q13: Daily Trend & Day-over-Day Comparison
SELECT 
    Day,
    COUNT(*) AS total_transactions,
    SUM(Class) AS fraud_transactions,
    ROUND((CAST(SUM(Class) AS REAL) / COUNT(*)) * 100.0, 4) AS fraud_rate_pct,
    ROUND(SUM(Amount), 2) AS total_volume_eur,
    ROUND(SUM(CASE WHEN Class = 1 THEN Amount ELSE 0 END), 2) AS fraud_exposure_eur,
    ROUND(AVG(CASE WHEN Class = 1 THEN Amount END), 2) AS avg_fraud_ticket_eur
FROM transactions
GROUP BY Day
ORDER BY Day ASC;


-- ----------------------------------------------------------------------------
-- QUERY 14: Transaction Risk Categories by Amount Brackets
-- Business Objective: Multi-bracket risk profile to optimize card authorization rules.
-- ----------------------------------------------------------------------------
-- Q14: Granular Amount Bracket Risk Stratification
SELECT 
    CASE 
        WHEN Amount < 25.0 THEN 'Bracket 1: Under €25'
        WHEN Amount < 100.0 THEN 'Bracket 2: €25 - €99.99'
        WHEN Amount < 300.0 THEN 'Bracket 3: €100 - €299.99'
        WHEN Amount < 1000.0 THEN 'Bracket 4: €300 - €999.99'
        ELSE 'Bracket 5: €1,000+'
    END AS amount_tier,
    COUNT(*) AS volume,
    SUM(Class) AS fraud_count,
    ROUND((CAST(SUM(Class) AS REAL) / COUNT(*)) * 100.0, 4) AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN Class = 1 THEN Amount ELSE 0 END), 2) AS total_fraud_loss_eur
FROM transactions
GROUP BY amount_tier
ORDER BY MIN(Amount) ASC;


-- ----------------------------------------------------------------------------
-- QUERY 15: Fraud-Related Financial Exposure (Top 10 High-Impact Losses)
-- Business Objective: Identify top 10 single largest fraudulent transactions for recovery audit.
-- ----------------------------------------------------------------------------
-- Q15: Top 10 Fraud Losses & Exposure Concentration
SELECT 
    Transaction_ID,
    Day,
    Hour,
    ROUND(Amount, 2) AS fraud_amount_eur,
    ROUND((Amount * 100.0 / (SELECT SUM(Amount) FROM transactions WHERE Class = 1)), 2) AS pct_of_total_fraud_loss
FROM transactions
WHERE Class = 1
ORDER BY Amount DESC
LIMIT 10;

