# Axon Framework 4 → 5 Migration — Progress

> Single source of truth. A fresh session with zero prior context must read this file alone and resume exactly where the previous session stopped.
>
> **Update protocol:** rewrite the relevant section, THEN commit. Never split "did the work" and "wrote progress.md" across commits.

## Goal

AF5 codebase, **same architecture as AF4**, legacy event storage preserved. Standard build green at end of stabilization.

Intermediate phases leave the project non-compiling — by design. Per-target `isolated-<TargetName>` scopes (created by the external `axon4to5-isolatedtest` skill) keep verification scoped through phases 2–8. Stabilization drops every scope.

---

## ▶︎ RESUME HERE — read first

- **Current Migration Phase:** _e.g. `#2 — aggregate (iterative)`_
- **Phase status:** _pending / in-progress / awaiting-checkpoint / paused / complete_
- **Next action (one sentence):** _e.g. "Migrate aggregate `org.example.Faculty`."_
- **Exact recipe:** _e.g. `aggregate` with `target=org.example.Faculty`_
- **Exact verify call:**
  ```
  Skill: axon4to5-isolatedtest
  Inputs:
    target-name: Faculty
    build-file: <target>/pom.xml
    main-sources: [src/main/java/org/example/Faculty.java, …]
    test-sources: [src/test/java/org/example/FacultyTest.java]
    extra-deps: [axon-modelling, axon-eventsourcing, axon-test]
    cleanup: false
  ```
- **Awaiting user input?** _yes (and the question) / no_
- **Working tree at resume:** _clean — last commit `<sha>` is the previous item_
- **Last commit:** `<short-sha>` — `<subject>`

---

## Project metadata

- Target project: `<absolute-path>`
- Started / Last updated: `<dates>`
- Active branch: `<branch>`
- Build tool: _maven / gradle_

---

## Pinned user decisions

Frozen for the run. NEVER re-ask.

- **License:** _free-af5 / axoniq-commercial_
- **Wiring:** _spring-boot / framework-config_ (drives Path A vs Path B in every recipe)
- **Build tool:** _maven / gradle_
- **Commit cadence:** _per-item (default)_
- **Unsupported features detected at INIT:** _none / list (saga, deadline, …)_
- **Per-feature decision:** _one line per feature: `<feature>: accept-stays-af4 / pause / remove-first`_

---

## Phase status

Legend: `pending` · `in-progress` · `awaiting-checkpoint` · `complete` · `paused` · `skipped`

| # | Recipe | Mode | Status | Items done / total | Last commit |
|---|---|---|---|---|---|
| 1 | openrewrite | one-shot | pending | — | — |
| 2 | aggregate | iterative | pending | 0 / ? | — |
| 3 | event-processor | iterative | pending | 0 / ? | — |
| 4 | command-gateway | iterative | pending | 0 / ? | — |
| 5 | query-gateway | iterative | pending | 0 / ? | — |
| 6 | query-handler | iterative | pending | 0 / ? | — |
| 7 | interceptors | iterative | pending | 0 / ? | — |
| 8 | event-storage-engine | one-shot + config sweep | pending | 0 / ? | — |
| — | stabilization | — | pending | — | — |

> When a phase enters `in-progress`, fill its plan section below with the **complete enumerated list** of FQ classes — don't rely on a fresh session re-running discovery.

---

## Per-phase plan

### Migration Phase #1 — openrewrite

- Recipe(s) run: _e.g. `org.axonframework.migration.UpgradeAxon4ToAxoniq5`_
- Resolved version: _e.g. `5.1.0`_
- Diff stat summary: _N files changed_
- Behavior changes flagged: _verbatim_
- Commit: `<sha>` — `chore(af5-migration): apply OpenRewrite recipe …`

### Migration Phase #N — `<recipe>`

| # | FQ class | FQ test | Status | Commit |
|---|---|---|---|---|
| 1 | `<…>` | `<…>` | pending | — |

Statuses: `pending` · `in-progress` · `done` · `deferred: <reason>` · `blocked: <reason>`.

### Stabilization

- `./mvnw clean verify` (or `./gradlew clean build`) first run: _PASS / FAIL_
- Outstanding compile errors: _list with one-line cause + fix-in-sha_
- Outstanding test failures: _list_
- Deferred items folded forward: _list_
- Behavior changes confirmed by user: _list_
