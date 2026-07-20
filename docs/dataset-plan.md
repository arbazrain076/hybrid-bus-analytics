# Dataset Plan

Tracks data sourcing, the 100,000-record scale strategy, and row counts through the pipeline. Update as
ingestion progresses — see `.project/skills/data-engineering/SKILL.md`.

## Sources under consideration

| Source | Catalogue/type | Status | Est. record count | Notes |
|---|---|---|---|---|
| BODS-ARCHIVE Timetables (North West region, 1 Jul 2026) | Timetables (GTFS) | Downloaded | TBD after parsing | `data/raw/timetables/timetables-20260701.zip` -> `itm_north_west_gtfs_20260701.zip`; see ADR-002 |
| BODS-ARCHIVE SIRI-VM (national, 1 Jul 2026, filtered to Greater Manchester) | Location (SIRI-VM) | Downloaded | ~575k pings (est.) | `data/raw/sirivm/sirivm-20260701.zip`, 2,761 snapshots; filter to GM during ingestion; see ADR-002 |
| BODS Disruptions | Disruptions (SIRI-SX) | Not started (blocked — needs official BODS account) | | Deferred; not in current scope, see ADR-002 |
| Synthetic augmentation | Synthetic (Faker/SDV) | Rejected | | Student explicitly ruled out synthetic delay data; see ADR-002 |
| Supplementary dataset(s) | e.g. ONS/data.gov.uk | Not started | | Only if needed to reach 100k after real-data ingestion |

## Known constraint (resolved — see ADR-002)

Official BODS's Location feed (SIRI-VM) is real-time only with no DfT-maintained historical archive, and
every official BODS bulk-download page requires account registration. Resolved by using
`data.datalibrary.uk`'s BODS-ARCHIVE — a no-login, volunteer-run mirror that has been passively archiving
BODS output since 18 June 2025 — to obtain one day (1 July 2026) of real national SIRI-VM position
snapshots and real GTFS timetable snapshots, scoped to Greater Manchester. Real delay will be computed
from actual position pings vs. scheduled stop times, not synthetic data. Full reasoning in
`docs/architecture-decisions.md` ADR-002.

## Row count tracking

| Stage | Row count | Date | Notes |
|---|---|---|---|
| Raw (bronze), per source | sirivm zip: 2,761 files / 6,745,666,734 bytes; timetables zip: 11 files / 1,395,801,618 bytes | 2026-07-20 | File-level counts only — not yet parsed into rows |
| Post-join (silver) | | | Pending ingestion (Phase 2) |
| Post-augmentation (final) | | | No augmentation planned (real data only, per ADR-002) |

Target: >=100,000 in the final row.

## Data dictionary

Per-source field documentation goes here once ingestion starts (field name, type, source, meaning,
nullability).
