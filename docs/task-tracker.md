# Task Tracker

Kanban-style tracker mirroring `docs/implementation-roadmap.md`. Update via `/update-tracker`. Keep
completed items — this is a running record, not just current state.

## Backlog
- [ ] Task 2 — Define custom metric (if any) and justify against literature
- [ ] Task 4 — Set up Python env, requirements.txt, SparkSession smoke test
- [ ] Task 6 — Literature scan (5–8 sources)
- [ ] Task 9 — Pull Disruptions (SIRI-SX) data — blocked, see Blocked section
- [ ] Task 11/13 — Extract North West regional GTFS + document data dictionary

_(See `docs/implementation-roadmap.md` for the full 50-task list — pull tasks into this section as they
become actionable rather than duplicating the whole roadmap here up front.)_

## In Progress
- [ ] Task 12 — Real (non-synthetic) SIRI-VM + GTFS pulled for 1 July 2026; row counts pending PySpark
      parsing (Phase 2) to confirm >=100k threshold for the Greater Manchester scope.

## Done
- [x] Task 1 — Finalize stakeholder framing and problem statement. Ratified as ADR-001
      (`docs/architecture-decisions.md`): primary stakeholder Regional Transport Authority, secondary
      Bus Operators; problem = predict trip delay (minutes), translate to Service Reliability metrics for
      operational improvement + regulatory monitoring.
- [x] Task 3 — `.gitignore` created (data/raw, spark-warehouse, venv, .env, etc.). README skeleton still
      outstanding.
- [x] Task 7/8 — Explored BODS catalogues; confirmed official bulk downloads are account-gated. Found and
      used `data.datalibrary.uk` BODS-ARCHIVE (no-login mirror) instead. Ratified as ADR-002
      (`docs/architecture-decisions.md`).
- [x] Task 10 — Assessed historical AVL feasibility: resolved via BODS-ARCHIVE's passively-collected
      SIRI-VM snapshots (real data, not synthetic) — see ADR-002.
- [x] Task 14 — Raw data landed in `data/raw/` (bronze layer): `sirivm/sirivm-20260701.zip` (6.75GB,
      2,761 files), `timetables/timetables-20260701.zip` (1.40GB, 11 regional files). Both verified as
      valid, complete zips.

## Blocked
- [ ] BODS Disruptions (SIRI-SX) — needs an official BODS account (registration requires the student to
      act directly). Not currently in scope; revisit if the account is registered and Disruptions should
      be joined in later.
