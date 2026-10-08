-- Project 1: schema for the fictional custody database (PostgreSQL)
-- Run from the repo root:  psql -d custody -f sql/01_schema.sql
--
-- Note: trades has NO primary key and there are NO foreign keys on purpose.
-- This is a "landing" schema: it accepts the messy data exactly as received,
-- so your data-quality queries (04_data_quality_checks.sql) can find the problems.

DROP TABLE IF EXISTS client_positions, custodian_positions, settlements, trades,
    prices, counterparties, securities, accounts, clients CASCADE;

CREATE TABLE clients (
    client_id      TEXT PRIMARY KEY,
    client_name    TEXT NOT NULL,
    client_type    TEXT NOT NULL
);

CREATE TABLE accounts (
    account_id     TEXT PRIMARY KEY,
    client_id      TEXT NOT NULL,
    account_name   TEXT NOT NULL,
    base_currency  CHAR(3) NOT NULL
);

CREATE TABLE securities (
    security_id    TEXT PRIMARY KEY,
    isin           CHAR(12),            -- nullable on purpose: some are missing
    ticker         TEXT NOT NULL,
    security_name  TEXT NOT NULL,
    asset_class    TEXT NOT NULL,
    currency       CHAR(3) NOT NULL,
    market         TEXT NOT NULL
);

CREATE TABLE counterparties (
    counterparty_id    TEXT PRIMARY KEY,
    counterparty_name  TEXT NOT NULL
);

CREATE TABLE prices (
    security_id    TEXT NOT NULL,
    price_date     DATE NOT NULL,
    close_price    NUMERIC(18,4) NOT NULL,
    PRIMARY KEY (security_id, price_date)
);

CREATE TABLE trades (
    trade_id         TEXT NOT NULL,     -- not unique on purpose: duplicates exist
    account_id       TEXT NOT NULL,
    security_id      TEXT NOT NULL,
    counterparty_id  TEXT NOT NULL,
    trade_date       DATE NOT NULL,
    settle_date      DATE NOT NULL,
    side             TEXT NOT NULL,
    quantity         NUMERIC(18,0) NOT NULL,
    price            NUMERIC(18,4) NOT NULL,
    currency         CHAR(3) NOT NULL,
    trade_value      NUMERIC(20,2) NOT NULL
);

CREATE TABLE settlements (
    trade_id              TEXT PRIMARY KEY,
    expected_settle_date  DATE NOT NULL,
    actual_settle_date    DATE,
    status                TEXT NOT NULL,   -- SETTLED / FAILED / PENDING
    fail_reason           TEXT,            -- set if the trade failed at any point
    days_late             INTEGER
);

CREATE TABLE custodian_positions (
    position_date  DATE NOT NULL,
    account_id     TEXT NOT NULL,
    security_id    TEXT NOT NULL,
    isin           CHAR(12),
    quantity       NUMERIC(18,0) NOT NULL,
    market_value   NUMERIC(20,2) NOT NULL,
    currency       CHAR(3) NOT NULL
);

CREATE TABLE client_positions (
    position_date  DATE NOT NULL,
    account_id     TEXT NOT NULL,
    security_id    TEXT NOT NULL,
    quantity       NUMERIC(18,0) NOT NULL
);
