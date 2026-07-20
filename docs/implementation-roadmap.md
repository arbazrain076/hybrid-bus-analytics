# Implementation Roadmap

50-task roadmap for the Hybrid Bus Reliability and Delay Prediction Platform. Living document — check off
tasks as completed and keep in sync with `docs/task-tracker.md` (via `/update-tracker`). Phases roughly
mirror the marking components in `docs/assignment-compliance-matrix.md`.

## Phase 0 — Setup & Planning (1–6)
- [ ] 1. Finalize stakeholder + problem framing (delay prediction for Transport Authority/Operator)
- [ ] 2. Define custom metric (if any) and justify against literature
- [ ] 3. Set up git repo structure, `.gitignore`, README skeleton
- [ ] 4. Set up Python env, `requirements.txt`, SparkSession smoke test
- [ ] 5. Set up project task tracking (`docs/task-tracker.md`)
- [ ] 6. Literature scan: 5–8 sources on transport delay prediction / smart cities

## Phase 1 — Data Acquisition (7–14)
- [ ] 7. Explore BODS catalogues (Timetables, Disruptions, Location); confirm accessible formats
- [ ] 8. Pull sample Timetables (TransXChange/GTFS) data for target region/operators
- [ ] 9. Pull Disruptions (SIRI-SX) data
- [ ] 10. Assess historical AVL/location data feasibility; decide live-poll vs synthetic
- [ ] 11. Design synthetic delay-augmentation approach (Faker/SDV), grounded in timetable structure
- [ ] 12. Generate/collect data until >=100,000 records; log row counts per source
- [ ] 13. Document data dictionary for each source table
- [ ] 14. Store raw data (bronze layer) as Parquet/CSV in `data/raw`

## Phase 2 — Ingestion & Cleaning (PySpark) (15–22)
- [ ] 15. Initialize SparkSession with >=4 partitions, documented
- [ ] 16. Load raw datasets into PySpark DataFrames; validate/define schemas
- [ ] 17. Null/missing value profiling and handling strategy per column
- [ ] 18. Standardize date/time formats and timezones across sources
- [ ] 19. Deduplicate and detect outliers (IQR/z-score) in timing fields
- [ ] 20. Join Timetables + Disruptions by Service Code/Operator; document join strategy
- [ ] 21. Repartition/cache DataFrames at key stages; capture before/after partition counts
- [ ] 22. Persist cleaned (silver layer) data to Parquet + load subset into SQL database

## Phase 3 — Database Layer (23–27)
- [ ] 23. Design relational schema + ER diagram
- [ ] 24. Implement schema creation scripts (SQLite/Postgres), no hardcoded creds
- [ ] 25. Write parameterised ingestion script: PySpark/Pandas -> DB
- [ ] 26. Write sample parameterised queries for report appendix
- [ ] 27. Export DB schema diagram + SQL dump for submission

## Phase 4 — Exploratory Data Analysis (28–32)
- [ ] 28. PySpark `describe`/`groupBy`/`agg` exploration of delay, headway, route volume
- [ ] 29. Compute mean/median/std/skewness/kurtosis via PySpark functions
- [ ] 30. Data quality report: null counts, cardinality, outlier detection summary
- [ ] 31. Convert key aggregates to Pandas for matplotlib/seaborn/plotly visualizations
- [ ] 32. Produce distribution/correlation visualizations tied to the business problem

## Phase 5 — Feature Engineering & ML (33–40)
- [ ] 33. Define target variable (delay in minutes) and Travel Time Variability (CV) mapping
- [ ] 34. Feature engineering: time-of-day, day-of-week, route, operator, disruption flag, headway
- [ ] 35. Build PySpark ML pipeline: StringIndexer/OneHotEncoder, VectorAssembler
- [ ] 36. Time-based train/test split strategy, documented
- [ ] 37. Train Model 1: Linear Regression (baseline) with CrossValidator
- [ ] 38. Train Model 2: Random Forest Regressor with CrossValidator/ParamGrid
- [ ] 39. Train Model 3: Gradient-Boosted Tree Regressor with CrossValidator/ParamGrid
- [ ] 40. Evaluate all 3 models: RMSE/MAE/R², training time, Model Efficiency; compare

## Phase 6 — System Integration (41–44)
- [ ] 41. Assemble end-to-end pipeline script/orchestration
- [ ] 42. Capture Spark UI screenshots (partition utilisation, stage metrics) during a full run
- [ ] 43. (Optional) Build Streamlit dashboard: model comparison + delay prediction explorer
- [ ] 44. Security pass: confirm parameterised queries everywhere, no hardcoded secrets

## Phase 7 — Evaluation & Reflection (45–47)
- [ ] 45. Validate predictions against held-out/disruption records; write Validation section
- [ ] 46. Critical reflection: memory-vs-distributed trade-off, limitations, ethics/GDPR/bias
- [ ] 47. Algorithmic complexity (Big-O) write-up for chosen models vs alternatives

## Phase 8 — Report & Submission (48–50)
- [ ] 48. Draft full technical report per required structure; insert figures/screenshots; APA references
- [ ] 49. Assemble GitHub repo: code, configs, README, requirements.txt, docs folder, sample outputs
- [ ] 50. Final rubric self-check, viva prep, export PDF, submit via Campus 4.0 with correct file naming
