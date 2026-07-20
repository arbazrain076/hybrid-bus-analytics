# Hybrid Bus Reliability and Delay Prediction Platform

Individual coursework project (ST5011CEM, Big Data Programming Project) building a PySpark-based platform
that predicts bus trip delay and translates it into Service Reliability metrics for a Regional Transport
Authority and Bus Operators.

## Status

Project setup and initial data acquisition are in progress. See `docs/task-tracker.md` for the current
state and `docs/implementation-roadmap.md` for the full plan.

## Data

Real historical bus timetable (GTFS) and vehicle-position (SIRI-VM) data for Greater Manchester, sourced
from the Bus Open Data Service (BODS), Open Government Licence. Sourcing details and provenance are
documented in `docs/dataset-plan.md` and `docs/architecture-decisions.md` (ADR-002).

## Project structure

- `docs/` — planning docs: task tracker, roadmap, architecture decisions, dataset plan, report outline
- `data/` — raw and processed data (raw data is gitignored; see `docs/dataset-plan.md` for sourcing/regeneration steps)
- `src/` — pipeline code (ingestion, processing, ML, visualisation) — not yet added
- `sql/` — database schema and sample queries — not yet added

## Setup

Setup instructions (Python environment, `requirements.txt`, SparkSession configuration) will be added once
the environment is initialised (see `docs/task-tracker.md`).
