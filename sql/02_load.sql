-- Project 1: load the CSVs. Run from the repo root (paths are relative):
--   psql -d custody -f sql/02_load.sql
\copy clients             FROM 'data/clients.csv'             WITH (FORMAT csv, HEADER true)
\copy accounts            FROM 'data/accounts.csv'            WITH (FORMAT csv, HEADER true)
\copy securities          FROM 'data/securities.csv'          WITH (FORMAT csv, HEADER true)
\copy counterparties      FROM 'data/counterparties.csv'      WITH (FORMAT csv, HEADER true)
\copy prices              FROM 'data/prices.csv'              WITH (FORMAT csv, HEADER true)
\copy trades              FROM 'data/trades.csv'              WITH (FORMAT csv, HEADER true)
\copy settlements         FROM 'data/settlements.csv'         WITH (FORMAT csv, HEADER true)
\copy custodian_positions FROM 'data/custodian_positions.csv' WITH (FORMAT csv, HEADER true)
\copy client_positions    FROM 'data/client_positions.csv'    WITH (FORMAT csv, HEADER true)

-- Checkpoint: row counts
SELECT 'trades' AS table_name, COUNT(*) FROM trades
UNION ALL SELECT 'settlements', COUNT(*) FROM settlements
UNION ALL SELECT 'prices', COUNT(*) FROM prices
UNION ALL SELECT 'custodian_positions', COUNT(*) FROM custodian_positions
UNION ALL SELECT 'client_positions', COUNT(*) FROM client_positions;
