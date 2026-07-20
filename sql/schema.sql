-- Relational schema for the Hybrid Bus Reliability platform (see ADR-005).
-- SQLite dialect, kept PostgreSQL-portable (standard types, explicit foreign keys).
-- Referential integrity in SQLite requires `PRAGMA foreign_keys = ON;` per connection (set by the loader).

DROP TABLE IF EXISTS fact_delay_event;
DROP TABLE IF EXISTS dim_stop;
DROP TABLE IF EXISTS dim_operator;

-- Operator dimension: join key is the operator code (brief's "Service Code / Operator").
CREATE TABLE dim_operator (
    operator      TEXT PRIMARY KEY,
    operator_name TEXT
);

-- Stop dimension: location reference for each scheduled stop.
CREATE TABLE dim_stop (
    stop_id   TEXT PRIMARY KEY,
    stop_name TEXT,
    stop_lat  REAL,
    stop_lon  REAL
);

-- Delay-event fact table: one observed arrival with its reconstructed delay.
CREATE TABLE fact_delay_event (
    event_id      INTEGER PRIMARY KEY,
    service_date  TEXT    NOT NULL,
    operator      TEXT    NOT NULL,
    line          TEXT,
    direction_id  INTEGER,
    trip_id       TEXT,
    stop_id       TEXT,
    stop_sequence INTEGER,
    sched_sec     INTEGER,
    ping_sec      INTEGER,
    delay_min     REAL    NOT NULL,
    FOREIGN KEY (operator) REFERENCES dim_operator (operator),
    FOREIGN KEY (stop_id)  REFERENCES dim_stop (stop_id)
);

-- Indexes for the analytical queries in sql/sample_queries.sql.
CREATE INDEX idx_delay_operator ON fact_delay_event (operator);
CREATE INDEX idx_delay_line     ON fact_delay_event (line);
CREATE INDEX idx_delay_date     ON fact_delay_event (service_date);
