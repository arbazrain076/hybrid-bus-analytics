# Assignment Compliance Matrix

Living document. Update the Status/Evidence columns as work progresses — do not let this go stale. Cross-
checked by the `compliance-auditor` agent and `/check-compliance`.

**Status legend:** Not started | In progress | Done | Blocked

## Problem Definition & Topic Selection

| Requirement | Marking component | Status | Evidence location | Notes |
|---|---|---|---|---|
| Business stakeholder identified | 1 | Done | `docs/architecture-decisions.md` (ADR-001) | Primary: Regional Transport Authority; secondary: Bus Operators |
| Problem statement defined (what's predicted, how it's used) | 1 | Done | `docs/architecture-decisions.md` (ADR-001) | Predict trip delay (minutes); translate to Service Reliability metrics |
| Project title/application confirmed distinct from other students' work | 1 | Not started | | Not independently verifiable — requires student confirmation |

## Data Collection & Ingestion

| Requirement | Marking component | Status | Evidence location | Notes |
|---|---|---|---|---|
| Use open datasets (BODS or equivalent) | 1, 2 | Not started | | |
| Ingest timetable, disruption, location, and/or fare data | 1, 2 | Not started | | |
| Clean and preprocess into usable form | 2 | Not started | | |
| Meet >=100,000 record threshold (with documented augmentation if needed) | 1, 2 | Not started | `docs/dataset-plan.md` | |

## Data Storage & Processing

| Requirement | Marking component | Status | Evidence location | Notes |
|---|---|---|---|---|
| Relational DB or distributed DataFrame storage | 2, 4 | Not started | `sql/` | |
| PySpark for large-scale transforms; Pandas/Dask justified per stage | 2 | Not started | | |
| Dataset relationships/joins (Service Code/Operator) | 2 | Not started | | |
| Parameterised queries (SQL injection prevention) | 2, 4 | Not started | | |

## Analytics & Prediction

| Requirement | Marking component | Status | Evidence location | Notes |
|---|---|---|---|---|
| >=1 ML algorithm, >=3 models/configs within one category | 3 | Not started | `.project/templates/evaluation-table-template.md` output | |
| Predict delay / non-compliance / disruption patterns / peak hours | 3 | Not started | | |
| Evaluate against brief's reliability/efficiency metrics | 3, 6 | Not started | | |
| Evaluate algorithmic complexity and accuracy | 3 | Not started | | |
| MLlib pipeline documented (VectorAssembler, stages, CrossValidator) | 3 | Not started | | |

## System Development

| Requirement | Marking component | Status | Evidence location | Notes |
|---|---|---|---|---|
| Coherent software solution (not notebook dump) | 4 | Not started | | |
| Architecture diagram (ingestion -> processing -> model -> viz) | 4 | Not started | `docs/architecture-decisions.md`, report | |
| Optional dashboard | 4 | Not started | | Optional |

## Security & Professional Practice

| Requirement | Marking component | Status | Evidence location | Notes |
|---|---|---|---|---|
| Version control (Git/GitHub), repo link in submission | 4, 7 | Not started | | |
| No hard-coded credentials | 4 | Not started | | |
| SparkSession/DB config documented | 4 | Not started | README | |
| Ethical/social/legal reflection (GDPR, bias, security) | 6 | Not started | Report Critical Reflection | |

## Big Data Scale & Spark Evidence

| Requirement | Marking component | Status | Evidence location | Notes |
|---|---|---|---|---|
| >=4 partitions configured | 3, 4 | Not started | `docs/evidence-checklist.md` | |
| Caching and repartitioning demonstrated | 3, 4 | Not started | | |
| >=1 Spark UI screenshot (partition utilisation) | 3, 4, 7 | Not started | `outputs/spark_ui_screenshots/` | |
| Partition counts and stage metrics reported | 3, 4 | Not started | | |

## Evaluation & Critical Reflection

| Requirement | Marking component | Status | Evidence location | Notes |
|---|---|---|---|---|
| Thorough evaluation using defined metrics | 6 | Not started | | |
| Memory-vs-distributed trade-off reflection | 6 | Not started | Report Critical Reflection | Explicitly named in brief |
| Challenges/limitations/future work | 6 | Not started | | |
| Individual viva | 7 | Not started | `docs/viva-notes.md` | |

## Academic Integrity

| Requirement | Marking component | Status | Evidence location | Notes |
|---|---|---|---|---|
| All sources referenced (APA); tools acknowledged, excluding AI per brief | 7 | Not started | References section | See `.project/skills/academic-integrity/SKILL.md` |
| Project title/application genuinely distinct even though dataset (BODS) is shared | 1 | Not started | `docs/architecture-decisions.md` | Currently a provisional framing, not yet ratified |
| No uncredited reuse of external content (code, analysis, prior coursework) | 6, 7 | Not started | | |

## Report Structure (all mandatory except Literature Review)

| Section | Status | Notes |
|---|---|---|
| Cover Page | Not started | |
| Executive Summary (150-200 words) | Not started | |
| Introduction (incl. metric definitions, LOs targeted) | Not started | |
| Literature Review | Not started | Optional but encouraged |
| Data Collection & Preprocessing | Not started | |
| Methodology | Not started | |
| System Design and Implementation | Not started | |
| Results and Evaluation | Not started | |
| Critical Reflection | Not started | |
| Conclusion | Not started | |
| References (APA) | Not started | |
| Appendices | Not started | |

## Submission Requirements

| Requirement | Status | Notes |
|---|---|---|
| GitHub repo: code, configs, README, requirements.txt, scripts, docs folder, sample outputs | Not started | |
| Database export: SQL dump, schema diagram, sample queries | Not started | |
| Technical report PDF, correct file naming (NAME_studentID) | Not started | |
