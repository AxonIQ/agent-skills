---
last-updated: 2026-05-25
session-count: 1
---

## RESUME HERE

**Last completed:** IMP-016 — Eval coverage for new patterns
**Next action:** Backlog empty. Run another discovery pass when ready.
**Current session commit:** IMP-001..015, 017..019 committed; IMP-016 pending
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
| IMP-007 | Durability in SKILL.md | done | New Step 2.5 (~73 lines) adds `.axon4to5-migration/progress.md` schema; new behaviour rule mandates per-file progress commit. |
| IMP-008 | Detection — post-OR greps | done | 13 Partial patterns now have dual-form Detection (Pre-migration AF4 / Post-OpenRewrite partial). |
| IMP-009 | SKILL.md simplification | done | SKILL.md 430→297 lines (-31%); per-step verbatim import lists collapsed to pattern-file pointers + cross-phase couplings; description 186 chars. |
| IMP-010 | Examples import audit | done | 3 examples fixed: MetaData→Metadata in projector-with-dispatch; MessagingConfigurer canonical path in 2 native-configurer examples. Zero forbidden-name. |
| IMP-011 | Command-gateway top-level pattern | done | New `command-gateway-top-level.md` for REST/MCP/CLI dispatchers (keeps `CommandGateway`, .send().resultAs() shape). OR status: Partial. SKILL.md table + cross-ref in command-dispatcher.md updated. |
| IMP-012 | Discovery pass | done | Added IMP-013..IMP-018 below from re-comparison. |
| IMP-013 | Renumber duplicate examples in query-handlers/ | done | Renamed 10 files into a single sequential `01-handler-…05-handler-…06-caller-…10-caller-…` scheme; H1 numbers in 5 caller files updated to match. |
| IMP-014 | Cross-link patterns ↔ examples/java/ | done | 11 patterns gained a "Reference source:" line pointing at the matching `examples/java/af5/.../*.java` file. |
| IMP-015 | Move OR coverage table out of SKILL.md | done | 32-row table moved to `references/openrewrite-coverage.md`; SKILL.md slimmed to 265 lines (was 297). |
| IMP-016 | Eval coverage for new patterns (unblocked) | obsolete-row | See below for live row. |
| IMP-019 | Reconcile evals with flat-pattern skill design | done | 49 evals across 8 recipes had `prompt` + `skill_args` rewritten to drive the flat-pattern SKILL.md. `skill_args` now `{configuration, skip-openrewrite}`. RUN_EVALS_PROMPT.md + skill CLAUDE.md updated. Smoke-tested `run.py prep`. |
| IMP-016 | Eval coverage for new patterns | done | 3 new evals + fixtures: event-store/5 serializer-to-converter, aggregate/32 command-annotation, event-processor/9 event-bus-to-sink. query-response-types covered by query-gateway/2; command-gateway-top-level covered by command-gateway/2. Prep smoke-tested. |
| IMP-017 | Pattern Notes formatting consistency | done | 3/32 patterns normalised (29 already compliant); stray "## Notes (continued)" headers folded into single Notes section; OR-status + Reference-source bullets land at tail. |
| IMP-018 | `make check-attribution` target | done | New `make check-attribution` target uses `scripts/forbidden-names.txt` as a regex list; wired into `make check` so CI catches regressions. |

## Session Log

### Session 1 — 2026-05-25
- Initialized progress file and backlog.
- IMP-001 done: SKILL.md Step 4 rewritten — compile-driven validation; grep demoted to leftover audit; new behaviour rule.
- IMP-002 done: Partial-migration-state sections added to aggregate-class, command-handler, aggregate-lifecycle, namespace-routing, test-fixture; README + SKILL.md note idempotency.
- IMP-003 done: Makefile (`generate`, `check`, `help`); script regenerates catalog table inside `patterns/README.md` between markers; SKILL.md rule added forbidding hand edits to generated files.
- IMP-004 done: SKILL.md gained "What OpenRewrite covers" sub-section (27-row table); every pattern Notes section ends with "OpenRewrite status:" tagged Full / Partial / None grounded in YAML rule names. Reconciled aggregate-lifecycle.md + command-handler.md partial sections (IMP-002 assumed OR didn't rewrite apply() — actually does via ReplaceAggregateLifecycleApply).
- IMP-005 done: examples/java/{af4,af5}/ holds 12 real Heroes Java files (aggregate + projector + REST + test pair); java/README.md is a pairs table; generator now skips Java package subtrees without markdown.
- IMP-006 done: 4 new patterns — `serializer-to-converter`, `command-annotation`, `event-bus-to-sink`, `query-response-types`; SKILL.md coverage table got 4 new rows.
- IMP-007 done: SKILL.md Step 2.5 added — `.axon4to5-migration/progress.md` schema with RESUME HERE block, Pinned Decisions, Phase status table, per-phase items, Blockers; behaviour rule mandates per-file persist.
- IMP-008 done: every Partial-tagged pattern's Detection section is dual-form (Pre-migration AF4 grep + Post-OpenRewrite partial-state grep). 13 patterns touched.
- IMP-009 done: SKILL.md cut 31% (430→297 lines); verbatim AF4→AF5 enumerations replaced by pattern-file pointers + cross-phase coupling notes. description: 186 chars.
- IMP-010 done: 3 example files fixed — `MetaData`→`Metadata`, `MessagingConfigurer` canonical path. Zero forbidden-attribution hits.
- IMP-011 done: new `command-gateway-top-level.md` pattern for REST/MCP/CLI dispatchers (keeps `CommandGateway`, switches to `.send().resultAs(...)`); cross-ref from `command-dispatcher.md`; OR status: Partial.
- IMP-012 done: discovery pass — added IMP-013..IMP-018 to backlog (renumber duplicate examples; cross-link patterns to examples/java/; move OR coverage table to references/; eval coverage for new patterns; Notes formatting consistency; CI gate against forbidden attribution).
- IMP-013 done: query-handlers examples renumbered into a single 01..10 sequence (`01-handler-…` through `10-caller-…`); H1 lines kept in sync.
- IMP-014 done: 11 patterns now carry a `**Reference source:**` line pointing to the matching real-world `examples/java/af5/.../*.java` file.
- IMP-018 done (out of sequence — small CI gate): `make check-attribution` target + `scripts/forbidden-names.txt` regex list; `make check` chains generate + attribution gate + staleness diff.
- IMP-015 done: 32-row OR coverage table moved to `references/openrewrite-coverage.md`; SKILL.md now 265 lines and points at the per-pattern `OpenRewrite status:` line.
- IMP-017 done: Notes sections normalised (29/32 already compliant); 3 patterns lost stray "## Notes (continued)" headers and ended up with OpenRewrite status + Reference source bullets at the tail.
- IMP-016 blocked, IMP-019 seeded: eval infrastructure targets an older recipe-driven SKILL.md ("invoke the orchestrator with `mode=single source=…`"). Adding evals for the 5 new patterns needs eval prompts/infra rewritten to drive the current flat-phase design first (IMP-019). Marking IMP-016 blocked rather than authoring evals against a design mismatch.
- IMP-019 done: 49 evals across 8 recipes rewritten — `prompt` body re-templated to load SKILL.md + ALL_IN_ONE.md, skip Step 1/Step 2.5, cite specific pattern files; `skill_args` reduced to `{configuration, skip-openrewrite}`. RUN_EVALS_PROMPT.md + skill CLAUDE.md aligned. Smoke-tested `run.py prep` for aggregate eval 1. IMP-016 now unblocked.
- IMP-016 done: 3 new evals + fixtures — `event-store/5 spring-axoniq-serializer-to-converter` (SerializerConfig.java), `aggregate/32 spring-axoniq-command-annotation` (ShipOrderCommand.java), `event-processor/9 spring-axoniq-event-bus-to-sink` (ExternalEventPublisher.java). query-response-types and command-gateway-top-level already covered by existing query-gateway/2 and command-gateway/2 evals.
