# Axon Framework 4 → 5 Migration — index

This directory holds the migration state for this project. The orchestrator
(skill `axon4to5-migration`) reads and writes here. The skill works
for both Spring Boot and plain framework-configuration projects — the
**`wiring`** pinned decision in `progress.md` selects which path each
recipe runs.

## Files

- **`progress.md`** — single source of truth for migration state. Read this
  first to see where the migration is and what's next. The ▶︎ RESUME HERE
  block tells you the next move. The Pinned-decisions block records the
  `wiring` choice (`spring-boot` or `framework-config`) so every recipe
  picks Path A or Path B without re-asking. Rewritten alongside every
  code-changing commit so a fresh session can resume from the file alone.

- **`learnings.md`** — append-only narrative. Surprises, manual fixes,
  decisions worth remembering. Read on demand only.

> SQL / DDL / data migration is out of scope — this skill rewrites code
> only. The `event-storage-engine` recipe flags JPA schema changes in
> `learnings.md`; the user owns the schema/data move out-of-band on
> their own database.

This directory may grow over time. Keep `progress.md` and `learnings.md`
self-explanatory so a fresh session can reorient with no prior context.
