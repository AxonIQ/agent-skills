---
last-updated: 2026-05-25
session-count: 1
---

## RESUME HERE

**Last completed:** IMP-006 — Pattern gap audit
**Next action:** Start IMP-007: Durability in SKILL.md
**Current session commit:** IMP-001..005 committed; IMP-006 pending
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
| IMP-003 | Script parity / Makefile | done | Makefile added (generate/check/help); script regenerates patterns/README.md catalog between markers; SKILL.md rule added. |
| IMP-004 | OpenRewrite coverage mapping | done | SKILL.md has 27-row coverage table; every pattern has OpenRewrite status line. 12 Full / 11 Partial / 4 None. Also reconciled aggregate-lifecycle.md + command-handler.md partial-state sections against ReplaceAggregateLifecycleApply evidence. |
| IMP-005 | Real Java code examples | done | 12 Heroes Java files copied (6 AF4 + 6 AF5) covering aggregate/projector/REST/test; java/README.md pairs table; generator skips empty subtrees. |
| IMP-006 | Pattern gap audit | done | 4 new patterns: serializer-to-converter, command-annotation, event-bus-to-sink, query-response-types. SKILL.md coverage table updated. |
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
- IMP-003 done: Makefile (`generate`, `check`, `help`); script regenerates catalog table inside `patterns/README.md` between markers; SKILL.md rule added forbidding hand edits to generated files.
- IMP-004 done: SKILL.md gained "What OpenRewrite covers" sub-section (27-row table); every pattern Notes section ends with "OpenRewrite status:" tagged Full / Partial / None grounded in YAML rule names. Reconciled aggregate-lifecycle.md + command-handler.md partial sections (IMP-002 assumed OR didn't rewrite apply() — actually does via ReplaceAggregateLifecycleApply).
- IMP-005 done: examples/java/{af4,af5}/ holds 12 real Heroes Java files (aggregate + projector + REST + test pair); java/README.md is a pairs table; generator now skips Java package subtrees without markdown.
- IMP-006 done: 4 new patterns — `serializer-to-converter`, `command-annotation`, `event-bus-to-sink`, `query-response-types`; SKILL.md coverage table got 4 new rows.
