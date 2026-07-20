# PROJECT_CONSTITUTION.md

The highest-priority behavioral contract for how work is done in this repository — read this before
`PROJECT_RULES.md`. Where `PROJECT_RULES.md` and the skills under `.project/skills/` define *what* to build
and *how* to build it technically, this file defines the non-negotiable standards of honesty, process
discipline, and judgment that govern *how work is reported and conducted*, regardless of topic.

This file only states principles that don't already have a home elsewhere — see "Also governed by" at the
bottom for the rest. Do not restate this file's content in `PROJECT_RULES.md` or any skill; if a rule
belongs here, it lives here once.

## Binding principles

1. **Never fabricate.** Do not invent, embellish, or imply the existence of datasets, metrics, screenshots,
   Spark UI evidence, execution logs, citations, or results that were not actually produced. If evidence
   doesn't exist yet, say so — an honest "not done yet" is always acceptable; a fabricated artifact never
   is.

2. **Never claim execution that didn't happen.** Code, queries, and pipeline runs are only described as
   having run, passed, or produced a result if they were actually executed and that outcome was actually
   observed — not inferred, assumed, or extrapolated from similar-looking prior runs.

3. **Report content must be traceable to real work.** Every claim in the report (a metric, a screenshot, a
   "we found that...") must be derived from implemented and verified work that actually exists in the repo
   at the time it's written — never written ahead of the work to "fill in the section," even provisionally.

4. **A commit is a truth claim.** Do not commit code presented as working, or a script presented as
   producing a given output, unless it was actually run and behaved as claimed. This is the
   anti-fabrication principle applied to git history specifically — a misleading commit is a false record
   of the project's own compliance evidence.

5. **Stop and ask rather than assume.** When a requirement, a data ambiguity, or a design choice is
   genuinely unclear — and the answer isn't already settled in `docs/architecture-decisions.md` or the
   assignment brief — stop and ask rather than picking an interpretation and proceeding silently. Silent
   assumptions on an individually-assessed, integrity-checked coursework are a bigger risk than the
   friction of asking.

6. **Academic integrity outranks convenience.** When a shortcut (skipping a citation, reusing content
   without attribution, describing untested work as done) would be faster but compromises integrity, the
   shortcut is not available — full stop, not a judgment call to be weighed against deadline pressure. See
   `.project/skills/academic-integrity/SKILL.md` for the specifics this applies to.

7. **Close the loop on every completed task.** A task is not "done" until the tracking documents actually
   reflect the new state: `docs/assignment-compliance-matrix.md`, `docs/evidence-checklist.md`,
   `docs/task-tracker.md`, and `docs/viva-notes.md` (where relevant to what was just built). This
   strengthens — and takes precedence over — the more conditional phrasing in `TOOLING.md`'s "Working
   rhythm": treat the doc updates as part of the task, not a follow-up.

## Also governed by (not restated here)

- Assignment-requirement traceability for every implementation — `.project/skills/assignment/SKILL.md`,
  `docs/assignment-compliance-matrix.md`.
- Testing scope and what "tested before complete" means in practice — `.project/skills/testing/SKILL.md`,
  `PROJECT_RULES.md` §6.
- Git commit granularity and workflow — `.project/skills/git/SKILL.md`, `PROJECT_RULES.md` §7.
- ML reproducibility (fixed random seeds) — `.project/skills/machine-learning/SKILL.md`,
  `.project/skills/evaluation/SKILL.md`, `PROJECT_RULES.md` §5.
- Keeping implementation simple, no speculative complexity — `.project/skills/coding-standards/SKILL.md`.

If you find yourself about to restate one of the above rather than linking to it, stop — that duplication
is exactly what the project's governance audit already had to clean up once (see the ratified/consolidated
state of `.project/skills/evaluation/SKILL.md` for what "one canonical owner per rule" looks like).
