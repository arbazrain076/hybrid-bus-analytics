# Architecture Decisions

Index/log of ADRs for this project. Append new entries using
`.project/templates/architecture-decision-template.md` via `/log-decision` — never overwrite prior entries.

## Provisional decisions — pending ratification

These choices are currently assumed in the skills/docs below so work isn't blocked, but they have **not**
been formally ratified via an ADR yet. Treat every reference to them elsewhere in the repo as provisional,
not settled. Ratify each (or replace it) with a proper ADR entry in the Log below before/during the phase
that depends on it (see `docs/implementation-roadmap.md`).

| Decision | Currently assumed | Referenced in | Needed by |
|---|---|---|---|
| ML category | Regression (predict delay in minutes) | `TOOLING.md`, `.project/skills/machine-learning/SKILL.md`, `.project/skills/evaluation/SKILL.md`, `.project/skills/feature-engineering/SKILL.md` | Phase 5 |
| Compared models | Linear Regression, Random Forest Regressor, GBTRegressor | `.project/skills/machine-learning/SKILL.md` | Phase 5 |
| Database engine | SQLite (dev), Postgres-portable schema | `.project/skills/database/SKILL.md` | Phase 3 |

## Log

### ADR-001: Primary stakeholder and problem framing

**Date:** 2026-07-20
**Status:** Accepted

#### Context
The project needed one unambiguous business stakeholder and problem statement (brief's Project Topic
Selection requirement) instead of the placeholder "Transport Authority / Bus Operator" framing carried
through the governance-setup phase. Marking Component 1 (Problem Definition, Planning, and Dataset
Selection) and the report's Introduction both require a specific, defensible answer, not a
slash-separated placeholder.

#### Decision
- **Primary stakeholder:** Regional Transport Authority.
- **Secondary stakeholder:** Bus Operators (beneficiaries of the same predictions, not the primary driver
  of the analysis).
- **Problem statement:** predict bus trip delay (in minutes), and translate those predictions into the
  brief's Service Reliability metrics, to support two uses: operational improvement (operators act on
  delay-prone routes/times) and regulatory monitoring (the authority tracks operator compliance against
  reliability thresholds).

#### Alternatives considered
- Bus Operator as primary stakeholder (own-fleet scheduling optimisation) — rejected as primary because
  it frames the project around a single operator's routes rather than reliability oversight across
  operators, which fits the project's "Reliability" framing less well; kept as secondary instead.
- Commuter/Passenger App stakeholder (real-time arrival prediction) — rejected: shifts the problem toward
  live inference/UX rather than the batch, compliance-oriented analysis this project is built around.

#### Consequences
- The ML category (regression, predicting delay in minutes) and the target metric (Travel Time
  Variability / Service Reliability) remain the natural fit given this framing, but are still tracked
  separately as provisional in the table above until ratified at Phase 5.
- Report Introduction, Executive Summary, and stakeholder-facing framing throughout the project should
  now use this exact framing rather than "Transport Authority / Bus Operator".
- Distinctiveness of this framing versus other students' submissions (per
  `.project/skills/academic-integrity/SKILL.md`) still needs to be confirmed by the student — not
  independently verifiable and needs student confirmation.

#### Related
`docs/task-tracker.md` Task 1 (Phase 0); `docs/assignment-compliance-matrix.md` Problem Definition &
Topic Selection section; `docs/viva-notes.md` Problem Definition & Dataset Selection section.

### ADR-002: Data source — real AVL/timetable data via BODS-ARCHIVE mirror, Greater Manchester scope

**Date:** 2026-07-20
**Status:** Accepted

#### Context
`docs/dataset-plan.md`'s original assumption (Phase 0) was official BODS Timetables + Disruptions access,
with synthetic delay augmentation to cover BODS Location's known gap: SIRI-VM is a live-only feed with no
DfT-maintained historical archive, so there was no ready source of real "actual arrival" data to diff
against schedule. In practice, every official BODS bulk-download page (Timetables, Disruptions, Location,
Fares) requires a registered account, which the student would need to set up directly. Separately, the
student explicitly ruled out both synthetic delay data ("i dont need
synthetic data") and a week-long live-AVL polling collection to build a historical archive from scratch
("i dont have time to collect data for a week via api key").

#### Decision
Use `data.datalibrary.uk`'s "BODS-ARCHIVE" — a small, volunteer-run, OGL-licensed mirror that has been
passively archiving official BODS output since 18 June 2025 (daily national GTFS timetable snapshots;
national SIRI-VM vehicle-position snapshots every ~30 seconds) — with no account/API key required.
Downloaded the most recent fully-populated day, **1 July 2026**:
- `sirivm-20260701.zip` — 6.75 GB, 2,761 nested 30-second national SIRI-VM snapshots — `data/raw/sirivm/`
- `timetables-20260701.zip` — 1.40 GB, 11 regional GTFS files (national) — `data/raw/timetables/`

Analysis will scope to the **North West region file** (`itm_north_west_gtfs_20260701.zip`, covers Greater
Manchester/TfGM), filtering the national SIRI-VM snapshots down to Greater Manchester vehicles during
PySpark ingestion. Real observed delay will be computed by matching AVL position pings to scheduled stop
times — not via synthetic augmentation.

#### Alternatives considered
- Official BODS Timetables + Disruptions direct — rejected for now: needs the student to register an
  account (not yet done) and still has no historical AVL archive, so delay would still need synthetic
  augmentation on top.
- TfGM's own always-open GTFS/TransXChange feed alone — rejected as sole source: schedule-only, still
  requires synthetic delay augmentation, which the student ruled out.
- Synthetic delay augmentation grounded in timetable structure (the original Phase 0 assumption) —
  rejected per explicit student instruction.
- Live-polling the BODS AVL/GTFS-RT API ourselves to build a historical archive — rejected per explicit
  student instruction (no time for week-long collection).

#### Consequences
- Delay computation now requires real spatial/temporal matching between raw SIRI-VM XML position pings
  and GTFS scheduled stop times — more PySpark ingestion/cleaning work than synthetic augmentation would
  have been, but yields genuinely observed delay values, which is stronger evaluation/report material.
- Provenance must be reported honestly: BODS-ARCHIVE is an **unofficial third-party mirror** of official
  DfT/BODS open data (same OGL licence, ultimate source is still BODS) — cite it as such in References,
  not as if it were the official BODS portal.
- Single-day scope (1 July 2026) — comfortably clears the 100k-record floor for Greater Manchester alone
  (~300 active vehicles x 16h x 120 pings/hour is of that order), but temporal coverage is one day only;
  revisit/supersede this ADR if more days are later pulled.
- Official BODS Disruptions (SIRI-SX) is **not** included in this pull — still gated behind account
  registration. This is a documented gap vs. the original Phase 1 plan; revisit if account access happens.
- `data/raw/` added to `.gitignore` (too large to commit) — this ADR plus the exact source URLs is the
  reproduction record, per `.project/skills/git/SKILL.md` on documenting regeneration steps in lieu of
  committing raw data.

#### Related
`docs/task-tracker.md` Phase 1 (Tasks 7-14); `docs/dataset-plan.md`; `docs/assignment-compliance-matrix.md`
Data Collection & Ingestion section; ADR-001 (stakeholder framing this scope choice reinforces).
