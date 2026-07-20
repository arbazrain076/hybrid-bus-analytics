# Entity–Relationship Diagram

Relational schema for the delay-analysis database (see `schema.sql` and ADR-005). A star schema: the
`fact_delay_event` table references two dimensions via foreign keys (`operator`, `stop_id`).

```mermaid
erDiagram
    dim_operator ||--o{ fact_delay_event : "operator"
    dim_stop     ||--o{ fact_delay_event : "stop_id"

    dim_operator {
        TEXT operator PK
        TEXT operator_name
    }
    dim_stop {
        TEXT stop_id PK
        TEXT stop_name
        REAL stop_lat
        REAL stop_lon
    }
    fact_delay_event {
        INTEGER event_id PK
        TEXT    service_date
        TEXT    operator FK
        TEXT    line
        INTEGER direction_id
        TEXT    trip_id
        TEXT    stop_id FK
        INTEGER stop_sequence
        INTEGER sched_sec
        INTEGER ping_sec
        REAL    delay_min
    }
```

Loaded counts (2 service days, see `scripts/load_db.py`): dim_operator = 18, dim_stop = 7,765,
fact_delay_event = 150,955. Foreign-key check passes with 0 violations.
