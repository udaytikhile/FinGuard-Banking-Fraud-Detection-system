-- ============================================================================
-- FinGuard - Banking Fraud Detection & Transaction Intelligence System
-- Database Schema: SQLite Relational Analytics Store
-- Table: transactions
-- Purpose: Optimized analytical schema with composite indices for rapid query
--          execution across financial exposure, temporal risk, and class auditing.
-- ============================================================================

DROP TABLE IF EXISTS transactions;

CREATE TABLE transactions (
    Transaction_ID  TEXT PRIMARY KEY,
    Time            REAL NOT NULL,
    Day             INTEGER NOT NULL,
    Hour            INTEGER NOT NULL,
    Amount          REAL NOT NULL,
    V1              REAL NOT NULL,
    V2              REAL NOT NULL,
    V3              REAL NOT NULL,
    V4              REAL NOT NULL,
    V5              REAL NOT NULL,
    V6              REAL NOT NULL,
    V7              REAL NOT NULL,
    V8              REAL NOT NULL,
    V9              REAL NOT NULL,
    V10             REAL NOT NULL,
    V11             REAL NOT NULL,
    V12             REAL NOT NULL,
    V13             REAL NOT NULL,
    V14             REAL NOT NULL,
    V15             REAL NOT NULL,
    V16             REAL NOT NULL,
    V17             REAL NOT NULL,
    V18             REAL NOT NULL,
    V19             REAL NOT NULL,
    V20             REAL NOT NULL,
    V21             REAL NOT NULL,
    V22             REAL NOT NULL,
    V23             REAL NOT NULL,
    V24             REAL NOT NULL,
    V25             REAL NOT NULL,
    V26             REAL NOT NULL,
    V27             REAL NOT NULL,
    V28             REAL NOT NULL,
    Class           INTEGER NOT NULL CHECK(Class IN (0, 1))
);

-- High-performance analytical indices
CREATE INDEX IF NOT EXISTS idx_transactions_class ON transactions(Class);
CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions(Amount);
CREATE INDEX IF NOT EXISTS idx_transactions_day_hour ON transactions(Day, Hour);
CREATE INDEX IF NOT EXISTS idx_transactions_class_amount ON transactions(Class, Amount);

