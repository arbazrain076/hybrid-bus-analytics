# Evidence Checklist

Concrete artifacts the brief requires as proof, separate from the report prose. Verified via
`/spark-evidence` and `/check-compliance` (using the `pyspark-reviewer` and `compliance-auditor` agents).

## Spark evidence
- [ ] SparkSession configured with >=4 partitions (documented in code + README)
- [ ] At least one `.cache()`/`.persist()` call, with matching `.unpersist()`
- [ ] At least one `.repartition()`/`.coalesce()` call, with before/after partition counts noted
- [ ] At least one `broadcast()` join, where applicable
- [ ] >=1 Spark UI screenshot showing partition utilisation — saved at
      `outputs/spark_ui_screenshots/`
- [ ] Stage/task metrics (task duration, shuffle size) recorded in an experiment log entry
- [ ] `.checkpoint()` usage (or explicit decision not to use it) documented and distinguished from
      intermediate Parquet writes
- [ ] `.explain()` output or Spark UI DAG view captured as lazy-evaluation/DAG evidence

## Database evidence
- [ ] Schema/ER diagram — `docs/` or `sql/`
- [ ] SQL dump / export — `sql/db_dump.sql`
- [ ] Sample parameterised queries — `sql/sample_queries.sql`
- [ ] Confirmed no string-concatenated SQL anywhere (checked by `security` skill / agent review)
- [ ] Data load confirmed batch (`executemany`/bulk insert), not row-by-row
- [ ] Referential integrity (foreign keys/constraints) enforced, or absence explicitly documented

## ML evidence
- [ ] >=3 models/configs compared, single category — evaluation table populated
      (`.project/templates/evaluation-table-template.md`)
- [ ] Time-based train/test split documented
- [ ] Fixed random seed documented for every stochastic training/tuning step
- [ ] Trivial baseline model included alongside the 3+ compared models
- [ ] Automated target-leakage guard test exists and passes
- [ ] Model Efficiency reported for every model, including the baseline
- [ ] MLlib pipeline stages documented

## System/architecture evidence
- [ ] Architecture diagram (ingestion -> processing -> model -> visualisation)
- [ ] README with setup instructions, SparkSession config, DB config documented
- [ ] `requirements.txt` present and accurate

## Report evidence
- [ ] Code execution screenshots included
- [ ] Spark UI screenshot(s) included in report (not just repo)
- [ ] All figures numbered and captioned
- [ ] References in APA style, covering every source/tool

## Reflection evidence
- [ ] Memory-vs-distributed trade-off explicitly discussed
- [ ] Ethics/GDPR/bias explicitly discussed
- [ ] Validation against real disruption/operator records described

## Submission evidence
- [ ] GitHub repo link included in submission
- [ ] File named `NAME_studentID`
- [ ] PDF format
