-- Export analysis-ready tables for Power BI (Project 4). Run from the repo root.
\copy (SELECT * FROM v_trades_clean) TO 'exports/trades_clean.csv' WITH (FORMAT csv, HEADER true)
\copy (SELECT * FROM settlements) TO 'exports/settlements.csv' WITH (FORMAT csv, HEADER true)
\copy (SELECT * FROM v_position_recon WHERE recon_status <> 'Matched') TO 'exports/position_breaks_sql.csv' WITH (FORMAT csv, HEADER true)
\copy securities TO 'exports/securities.csv' WITH (FORMAT csv, HEADER true)
\copy counterparties TO 'exports/counterparties.csv' WITH (FORMAT csv, HEADER true)
\copy accounts TO 'exports/accounts.csv' WITH (FORMAT csv, HEADER true)
\copy clients TO 'exports/clients.csv' WITH (FORMAT csv, HEADER true)
\copy (SELECT * FROM v_dq_summary ORDER BY rule) TO 'exports/dq_summary.csv' WITH (FORMAT csv, HEADER true)
