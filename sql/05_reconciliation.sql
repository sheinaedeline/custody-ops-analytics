-- Project 1: reconcile the custodian's positions with the client's own records.
-- FULL OUTER JOIN keeps rows that exist on only one side, which is exactly what a break is.

CREATE OR REPLACE VIEW v_position_recon AS
SELECT COALESCE(c.account_id, f.account_id)       AS account_id,
       COALESCE(c.security_id, f.security_id)     AS security_id,
       c.quantity                                  AS custodian_qty,
       f.quantity                                  AS client_qty,
       COALESCE(c.quantity, 0) - COALESCE(f.quantity, 0) AS difference,
       CASE
           WHEN c.security_id IS NULL      THEN 'Missing at custodian'
           WHEN f.security_id IS NULL      THEN 'Missing at client'
           WHEN c.quantity <> f.quantity   THEN 'Quantity break'
           ELSE 'Matched'
       END AS recon_status
FROM custodian_positions c
FULL OUTER JOIN client_positions f
    ON  f.account_id  = c.account_id
    AND f.security_id = c.security_id
    AND f.position_date = c.position_date;

-- Summary: how many positions in each status
SELECT recon_status, COUNT(*) AS positions
FROM v_position_recon
GROUP BY recon_status
ORDER BY positions DESC;

-- The breaks themselves, largest absolute difference first
SELECT *
FROM v_position_recon
WHERE recon_status <> 'Matched'
ORDER BY ABS(difference) DESC;
