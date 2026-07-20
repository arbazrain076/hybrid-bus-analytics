# Hybrid Bus Reliability and Delay Prediction Platform

Individual coursework project (ST5011CEM, Big Data Programming Project) building a PySpark-based platform
that predicts bus trip delay and translates it into Service Reliability metrics for a Regional Transport
Authority and Bus Operators.

## Status

Project setup and initial data acquisition are in progress.

## Data

Real historical bus timetable (GTFS) and vehicle-position (SIRI-VM) data for Greater Manchester, sourced
from the Bus Open Data Service (BODS), Open Government Licence.

## Project structure

- `src/config/` — centralised SparkSession/DB configuration
- `scripts/` — standalone entry-point scripts (smoke tests, one-off runs)
- `data/` — raw and processed data (raw data is gitignored — too large to commit)
- `sql/` — database schema and sample queries — not yet added

## Setup

Requires **Python 3.11** and **Java 17** (PySpark needs a JDK).

```
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

**SparkSession config**: `src/config/spark_session.py` sets `spark.sql.shuffle.partitions` and
`spark.default.parallelism` to 8 (project requires >=4 partitions), running in local mode.

**Environment note**: if a system-wide `SPARK_HOME` environment variable is already set to a different
Spark install, it will conflict with the `pyspark` version pinned in `requirements.txt` and cause a
`JavaPackage object is not callable` error. Unset `SPARK_HOME` for this project's shell session (don't
change it system-wide) before running any script here.

Verify the setup:
```
python scripts/smoke_test.py
```
