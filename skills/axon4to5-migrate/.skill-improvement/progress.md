---
last-updated: 2026-05-25
session-count: 1
---

## RESUME HERE

**Last completed:** IMP-002 — Idempotent patterns
**Next action:** Start IMP-003: Script parity / Makefile
**Current session commit:** 20efcde (IMP-001); IMP-002 pending
**Blocked items:** none

## Pinned Decisions

| Question | Answer | Rationale |
|----------|--------|-----------|
| External-tool attribution in skill files | Forbidden | CLAUDE.md hard rule — no foreign-product names in skill content |
| ALL_IN_ONE.md / ALL_EXAMPLES.md edits | Generator only | Hand edits will be overwritten |

## Backlog

| ID | Title | Status | Notes |
|----|-------|--------|-------|
| IMP-001 | Compile-error-driven validation | done | Step 4 rewritten: compile is definition-of-done; grep demoted to 4b audit; behaviour rule added. |
| IMP-002 | Idempotent patterns | done | 5 patterns + README + SKILL.md got "Partial migration state (post-OpenRewrite)" guidance, grounded in OR YAML rules. |
| IMP-003 | Script parity / Makefile | pending | |
| IMP-004 | OpenRewrite coverage mapping | pending | |
| IMP-005 | Real Java code examples | pending | |
| IMP-006 | Pattern gap audit | pending | |
| IMP-007 | Durability in SKILL.md | pending | |
| IMP-008 | Detection — post-OR greps | pending | |
| IMP-009 | SKILL.md simplification | pending | |
| IMP-010 | Examples import audit | pending | |
| IMP-011 | Command-gateway top-level pattern | pending | |
| IMP-012 | Discovery pass | pending | |

## Session Log

### Session 1 — 2026-05-25
- Initialized progress file and backlog.
- IMP-001 done: SKILL.md Step 4 rewritten — compile-driven validation; grep demoted to leftover audit; new behaviour rule.
- IMP-002 done: Partial-migration-state sections added to aggregate-class, command-handler, aggregate-lifecycle, namespace-routing, test-fixture; README + SKILL.md note idempotency.
