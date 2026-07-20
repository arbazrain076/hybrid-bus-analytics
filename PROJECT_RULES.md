# PROJECT_RULES.md

Permanent engineering standards for the Hybrid Bus Reliability and Delay Prediction Platform. These rules
are in force for the life of the project. `TOOLING.md` points here first — skills under `.project/skills/`
elaborate on individual topics but must not contradict this file. Full assignment source of truth:
`docs/assignment-brief.pdf` (see `docs/assignment-compliance-matrix.md` for the traceability mapping).

## 1. Technology policy (hybrid pipeline)

- **PySpark is mandatory** for all large-scale ingestion, transformation, and ML (MLlib). This is a
  graded requirement, not a preference.
- Pandas/Dask may only be used for: (a) small local prototyping on samples, (b) the final
  DataFrame → matplotlib/seaborn/plotly plotting conversion. Every such use must carry a one-line
  justification in code comments/docstrings AND a corresponding note in the report.
- Never silently swap PySpark for Pandas because it's more convenient — that is a direct violation of
  the brief's "Key Technology Requirement" and a scored risk (see `docs/evidence-checklist.md`).

## 2. Scale floor

- The final analysis dataset must contain **≥100,000 records**. Track running counts in
  `docs/dataset-plan.md` at every stage (raw → post-join → post-augmentation).
- Any augmentation (synthetic data, extended date range, multi-catalogue join, supplementary dataset)
  must be documented with method and justification — never silently generated.

## 3. Spark configuration & evidence

- SparkSession must be configured with **≥4 partitions**, documented in code and README.
- Every pipeline run that matters must demonstrate caching and repartitioning explicitly — not implicitly
  relying on defaults.
- Capture **at least one Spark UI screenshot** showing partition utilisation per major pipeline run, saved
  under `outputs/spark_ui_screenshots/`.
- Avoid `.collect()` or `.toPandas()` on full-size DataFrames — only on aggregated/small results.
- Distinguish Spark's own `.checkpoint()` (lineage truncation via a reliable checkpoint directory) from
  simply writing intermediate Parquet output — they are not the same thing. Document which is used, where,
  and why. Use `.explain()` / the Spark UI's DAG tab as the concrete evidence for lazy evaluation and DAG
  understanding, not just a verbal claim. See `.project/skills/pyspark/SKILL.md` for detail.

## 4. Database & security

- All datasets are joined by **Service Code / Operator** (or equivalent documented key) — never an
  undocumented ad hoc join.
- **Parameterised queries only.** No string-concatenated or f-string-built SQL, anywhere, ever.
- **No hard-coded credentials.** Connection strings and secrets come from environment variables or a
  gitignored config file — never committed literals.
- Load data in batches (e.g. `executemany`/bulk insert), not row-by-row, given the ≥100,000-record scale.
- Enforce referential integrity (foreign keys/constraints) between joined tables, or explicitly document
  why not (e.g. SQLite requires `PRAGMA foreign_keys = ON`).
- Document the persistence strategy (what gets checkpointed, what gets written to Parquet vs the
  relational DB, and why) in `docs/architecture-decisions.md`.

## 5. Machine learning

- Pick **one** category (classification, regression, or clustering) and compare **≥3 models or
  configurations** within it — never mix categories to hit the count.
- Use a **time-based train/test split** for anything involving trips/timetables to avoid leakage across
  correlated records — a random split is not acceptable for this data.
- Set and document a **fixed random seed** for every stochastic training/tuning step (CrossValidator
  folds, tree-based model randomness), so results are reproducible.
- Include a **trivial baseline** (e.g. predict scheduled time / zero delay, or predict the mean) alongside
  the 3+ compared models, to show the compared models actually add value.
- Report the category-appropriate metrics in full, plus **Model Efficiency**, for every model compared.
  The canonical definition of Model Efficiency (and of Algorithmic Efficiency) lives in
  `.project/skills/evaluation/SKILL.md` — do not redefine it elsewhere; reference it instead.
- Where MLlib is used, the pipeline (VectorAssembler, indexers/encoders, CrossValidator, etc.) must be
  documented, not just run.
- The ML category and target framing chosen for this project (see `docs/architecture-decisions.md` for
  current status) are **provisional until ratified** as an ADR — do not treat them as immutable before
  that happens.

## 6. Testing

- Automated tests are proportionate, not exhaustive: data cleaning functions, DB parameterised-query
  safety, a target-leakage guard (assert the target/post-outcome columns never appear among model input
  features), and one end-to-end smoke test on a sample. Do not chase coverage numbers on a 2000-word
  individual coursework.

## 7. Git & documentation

- This project uses a **single-branch (trunk-based) workflow** — commit directly to the main branch; no
  feature branches. This is a deliberate choice for a solo, sequential-roadmap project, not an oversight.
- Commit incrementally, in the sequence described in `docs/git-commit-plan.md` — never as a single dump.
- Every commit message states what changed and why (see
  `.project/templates/commit-message-template.md`).
- Tag the commit representing the submitted state (e.g. `submission`) once Phase 8/Final Submission is
  reached, so the exact submitted state is unambiguous. Do not rewrite history after tagging.
- `.gitignore` covers raw/processed data (if large), virtualenv, `spark-warehouse/`, and any `.env`/secret
  files — regeneration steps go in the README instead of committing the data itself.
- SparkSession settings and DB connection configuration must be documented in the README or a config
  file — not left implicit in code.

## 8. Report & reflection

- Report follows the exact structure required by the brief (see `docs/report-outline.md`) — no omitted
  sections, ~2000 words excluding references/appendix. `docs/report-outline.md`'s per-section budgets are
  the authoritative breakdown — keep them summing to the total if adjusted.
- Critical Reflection **must** address the memory-vs-distributed trade-off and ethics/GDPR/bias — these
  are named explicitly in the brief and are easy to lose marks on by being generic.
- Every non-trivial technical or data choice gets an ADR in `docs/architecture-decisions.md` using
  `.project/templates/architecture-decision-template.md` — the report's justifications should trace back
  to these, not be invented at write-up time. Until an ADR is logged, treat the underlying decision as
  provisional in any report/code that references it.

## 9. Academic integrity

- All submitted work must be the student's own; every source of information (data, literature, tools) is
  referenced in APA style. Per the brief, tool acknowledgment **excludes AI** — cite non-AI tools/
  libraries used, but AI assistance itself is not required to be cited as a source.
- Even where the underlying dataset overlaps with other students' work, the project title and analytical
  application must remain genuinely distinct.
- See `.project/skills/academic-integrity/SKILL.md` for full detail (citation practice, common mistakes,
  the distinct-application requirement).

## 10. Change control

- If any rule in this file needs to change, update it here first and note the reason — don't let practice
  drift silently away from what's written.
