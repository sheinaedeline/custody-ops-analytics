-- Project 1: data-quality checks. One query per rule; each returns the offending rows.
-- Run:  psql -d custody -f sql/03_data_quality_checks.sql
-- Compare your counts with data/_injected_issues.csv (the answer key).

-- DQ01 Completeness: securities with no ISIN
SELECT 'DQ01 missing ISIN' AS rule, security_id, ticker
FROM securities
WHERE isin IS NULL;

-- DQ02 Uniqueness: trade IDs that appear more than once
SELECT 'DQ02 duplicate trade_id' AS rule, trade_id, COUNT(*) AS copies
FROM trades
GROUP BY trade_id
HAVING COUNT(*) > 1
ORDER BY trade_id;

-- DQ03 Validity: settlement date before trade date
SELECT 'DQ03 settle before trade' AS rule, trade_id, trade_date, settle_date
FROM trades
WHERE settle_date < trade_date;

-- DQ04 Validity: zero or negative quantity
SELECT 'DQ04 non-positive quantity' AS rule, trade_id, quantity
FROM trades
WHERE quantity <= 0;

-- DQ05 Consistency: trade currency differs from the security's currency
SELECT 'DQ05 currency mismatch' AS rule, t.trade_id, t.currency AS trade_ccy, s.currency AS security_ccy
FROM trades t
JOIN securities s ON s.security_id = t.security_id
WHERE t.currency <> s.currency;

-- DQ06 Integrity: trades pointing at a security that doesn't exist
SELECT 'DQ06 orphan security_id' AS rule, t.trade_id, t.security_id
FROM trades t
LEFT JOIN securities s ON s.security_id = t.security_id
WHERE s.security_id IS NULL;

-- DQ07 Integrity: trades pointing at an account that doesn't exist (expect 0)
SELECT 'DQ07 orphan account_id' AS rule, t.trade_id, t.account_id
FROM trades t
LEFT JOIN accounts a ON a.account_id = t.account_id
WHERE a.account_id IS NULL;

-- DQ summary: one row per rule with a count (this is what a data-quality dashboard shows).
-- Saved as a view so Power BI can use it later (06_exports.sql).
CREATE OR REPLACE VIEW v_dq_summary AS
WITH checks AS (
    SELECT 'DQ01 missing ISIN' AS rule, COUNT(*) AS failures FROM securities WHERE isin IS NULL
    UNION ALL
    SELECT 'DQ02 duplicate trade_id', COUNT(*) FROM (
        SELECT trade_id FROM trades GROUP BY trade_id HAVING COUNT(*) > 1) d
    UNION ALL
    SELECT 'DQ03 settle before trade', COUNT(*) FROM trades WHERE settle_date < trade_date
    UNION ALL
    SELECT 'DQ04 non-positive quantity', COUNT(*) FROM trades WHERE quantity <= 0
    UNION ALL
    SELECT 'DQ05 currency mismatch', COUNT(*) FROM trades t
        JOIN securities s ON s.security_id = t.security_id WHERE t.currency <> s.currency
    UNION ALL
    SELECT 'DQ06 orphan security_id', COUNT(*) FROM trades t
        LEFT JOIN securities s ON s.security_id = t.security_id WHERE s.security_id IS NULL
    UNION ALL
    SELECT 'DQ07 orphan account_id', COUNT(*) FROM trades t
        LEFT JOIN accounts a ON a.account_id = t.account_id WHERE a.account_id IS NULL
)
SELECT rule, failures, CASE WHEN failures = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM checks;

SELECT * FROM v_dq_summary ORDER BY rule;

-- A clean view for analysis: one row per trade_id (first copy kept), valid quantity and dates.
-- ROW_NUMBER() numbers the copies of each trade_id; we keep copy number 1.
CREATE OR REPLACE VIEW v_trades_clean AS
WITH numbered AS (
    SELECT t.*, ROW_NUMBER() OVER (PARTITION BY trade_id ORDER BY trade_date) AS copy_no
    FROM trades t
)
SELECT trade_id, account_id, security_id, counterparty_id, trade_date, settle_date,
       side, quantity, price, currency, trade_value
FROM numbered
WHERE copy_no = 1
  AND quantity > 0
  AND settle_date >= trade_date;
