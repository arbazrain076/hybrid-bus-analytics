# Git Commit Plan

Planned commit sequence mirroring `docs/implementation-roadmap.md` phases. Update if the actual sequence
diverges — see `.project/skills/git/SKILL.md`.

## Planned sequence

1. Repo scaffolding (operating system: TOOLING.md, PROJECT_RULES.md, .project/, docs/) — this commit
2. Project setup (env, requirements.txt, SparkSession smoke test)
3. Data acquisition scripts (BODS pulls, augmentation)
4. PySpark ingestion + cleaning
5. Dataset joins + row-count logging
6. Database schema + parameterised load scripts
7. EDA (PySpark stats + visualisations)
8. Feature engineering
9. Model 1 (baseline) training + evaluation
10. Model 2 training + evaluation
11. Model 3 training + evaluation
12. Model comparison + domain metric mapping
13. Pipeline orchestration / end-to-end integration
14. Spark UI evidence capture
15. (Optional) dashboard
16. Report drafting (incremental, section by section)
17. Final polish + submission prep

## Actual log

_(fill in as commits are made — commit hash, date, what it covered, deviation from plan if any)_

## Final submission tag

This project commits directly to the main branch (single-branch/trunk-based workflow — see
`.project/skills/git/SKILL.md`; no feature branches are used). Once Phase 8/Final Submission is reached and
the repo/report/DB export are all finalized, tag the exact commit submitted (e.g. `git tag submission`)
and record it here so the submitted state is unambiguous:

- Tag: <not yet created>
- Commit hash: <pending>
- Date: <pending>

