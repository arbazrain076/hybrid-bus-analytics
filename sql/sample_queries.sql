-- Sample analytical queries over the relational schema (see ADR-005).
-- In application code these run as PARAMETERISED queries (values bound via '?', never string-formatted);
-- the :placeholder markers below show where a bound parameter goes for the report/appendix.

-- 1. Least reliable lines: mean delay and on-time rate (within +/-2 min) per operator+line.
SELECT f.operator, f.line,
       COUNT(*)                                          AS n_events,
       ROUND(AVG(f.delay_min), 2)                        AS mean_delay_min,
       ROUND(100.0 * AVG(CASE WHEN ABS(f.delay_min) <= 2 THEN 1 ELSE 0 END), 1) AS on_time_pct
FROM fact_delay_event f
GROUP BY f.operator, f.line
HAVING n_events >= 100
ORDER BY mean_delay_min DESC
LIMIT 20;

-- 2. Delay by scheduled hour of day (peak vs off-peak profile).
SELECT (sched_sec / 3600) % 24                           AS sched_hour,
       COUNT(*)                                          AS n_events,
       ROUND(AVG(delay_min), 2)                          AS mean_delay_min
FROM fact_delay_event
GROUP BY sched_hour
ORDER BY sched_hour;

-- 3. Operator-level reliability summary joined to operator names (referential-integrity join).
SELECT o.operator, o.operator_name,
       COUNT(*)                                          AS n_events,
       ROUND(AVG(f.delay_min), 2)                        AS mean_delay_min
FROM fact_delay_event f
JOIN dim_operator o ON f.operator = o.operator
GROUP BY o.operator, o.operator_name
ORDER BY mean_delay_min DESC;

-- 4. Parameterised lookup: all delay events for one operator on one service date.
--    Application form: query(conn, "... WHERE f.operator = ? AND f.service_date = ?", (operator, date))
SELECT f.line, f.trip_id, s.stop_name, f.stop_sequence, f.delay_min
FROM fact_delay_event f
JOIN dim_stop s ON f.stop_id = s.stop_id
WHERE f.operator = :operator
  AND f.service_date = :service_date
ORDER BY f.trip_id, f.stop_sequence;
