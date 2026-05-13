# Axon Framework 4 → 5 Migration — Progress

> Single source of truth for this project's migration. A fresh session
> with **zero prior context** must be able to read this file alone and
> resume exactly where the previous session stopped.
>
> **Update protocol:** rewrite the relevant section, THEN commit. Never
> split "did the work" and "wrote progress.md" across commits.

## Goal

Fully compiling, green-test codebase on AF5, **same architecture as AF4**:
- No DCB. Aggregate-centric model retained.
- No new patterns. Sagas / projections / messages unchanged in shape.
- Legacy event storage preserved — `AggregateBased…EventStorageEngine` reads
  existing event log.
- `./mvnw clean verify` green at end of stabilization.

Intermediate phases will leave the project non-compiling — by design.
Per-target `isolated-<TargetName>` scopes (Maven profile or Gradle source-set,
created by the external `axon4to5-isolatedtest` skill) keep verification
scoped through phases 2–8. Stabilization drops every `isolated-*` scope.

> Manual work is sometimes unavoidable. Out-of-scope features, custom
> subclasses, bespoke config may need user judgment. The migration runner records
> `blocked` / `deferred-to-stabilization` and keeps moving.

---

## ▶︎ RESUME HERE — read this first

The single block a fresh session needs to make the next move. Keep
**current** and **concrete** (FQ class names, exact commands).

- **Current Migration Phase:** _e.g. `Migration Phase #2 — aggregate (iterative)`_
- **Phase status:** _pending / in-progress / awaiting-checkpoint / paused / complete_
- **Next action (one sentence):** _e.g. "Migrate aggregate `org.example.Faculty`."_
- **Exact recipe:** _e.g. `aggregate` with `target=org.example.Faculty`_
- **Exact verification call (paste into Skill tool):**
  ```
  Skill: axon4to5-isolatedtest
  Inputs:
    target-name: Faculty
    build-file: <target>/pom.xml
    main-sources: [src/main/java/org/example/Faculty.java, …]
    test-sources: [src/test/java/org/example/FacultyTest.java]
    extra-deps:
      - org.axonframework:axon-modelling:${axon5.version}
      - org.axonframework:axon-eventsourcing:${axon5.version}
      - org.axonframework:axon-test:${axon5.version}
    cleanup: false
  ```
- **Awaiting user input?** _yes (and the question) / no_
- **Working-tree expectation at resume time:** _clean — last commit `<sha>` is the previous item. If dirty → previous session crashed mid-step._
- **Last commit recorded by migration runner:** `<short-sha>` — `<commit subject>`

---

## Project metadata

- **Target project:** `<absolute-path>`
- **Started:** `<YYYY-MM-DD>`
- **Last updated:** `<YYYY-MM-DD HH:MM>`
- **Active branch:** `<branch-name>`
- **Build tool:** _Maven / Gradle_

---

## Pinned user decisions

Frozen for the run. A fresh session must respect these without re-asking.

- **License target:** _free-af5 / axoniq-commercial — set at INIT_
- **Wiring:** _spring-boot / framework-config — set at INIT, drives Path A vs Path B in every recipe_
- **Build tool:** _maven / gradle — set at INIT, passed as `build-file` to the external `axon4to5-isolatedtest` skill_
- **Recipe scope (openrewrite):** _top-level / per-module subset (list)_
- **Unsupported features detected at INIT:** _none / list (saga, deadline …). Per-aggregate `@DeadlineHandler` is recorded under the affected aggregate's row as well._
- **Per-feature decision:** _one line per feature: `<feature>: accept-stays-af4 / pause / remove-first`_
- **Commit cadence:** _per-item (default) / per-phase squashed / no auto-commits_
- **Storage-engine path:** _A (Spring Boot) / B (framework-config) — set when reached. Each path may use JPA or Axon Server as a sub-path._

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
| 8 | event-storage-engine | one-shot + configuration sweep | pending | 0 / ? | — |
| — | stabilization | — | pending | — | — |

> When a phase enters `in-progress`, fill its detailed section below with the
> **complete enumerated plan** (every FQ class). Don't rely on a fresh session
> re-running discovery — files may move mid-migration.

---

## Per-phase plan

### Migration Phase #1 — openrewrite

- **Recipe(s) run:** _e.g. `org.axonframework.migration.UpgradeAxon4ToAxoniq5`_
- **Resolved version:** _e.g. `5.1.0`_
- **Diff stat summary:** _N files changed_
- **Behavior changes flagged:** _verbatim_
- **Commit:** `<short-sha>` — `chore(af5-migration): apply OpenRewrite recipe …`

### Migration Phase #2 — aggregate

| # | FQ aggregate | FQ test | Status | Commit |
|---|---|---|---|---|
| 1 | `org.example.Faculty` | `org.example.FacultyTest` | pending | — |

**Status legend:** `pending` · `in-progress` · `done` · `deferred: <reason>` · `blocked: <reason>`

**Verify call template (per item — passed to `axon4to5-isolatedtest`):**
```
Skill: axon4to5-isolatedtest
Inputs:
  target-name: <AggregateSimpleName>
  build-file: <target>/pom.xml | <target>/build.gradle(.kts)
  main-sources: [<aggregate + commands + events + child entities>]
  test-sources: [<FQTestClass file path>]
  extra-deps: [axon-modelling, axon-eventsourcing, axon-test]
  cleanup: false                              # true on the last successful run before commit
```

**Combined across migrated items:** invoke the skill once per `<AggregateSimpleName>` — each scope is independent (`isolated-Faculty`, `isolated-Calendar`, …). The skill augments existing scopes idempotently and never mutates sibling scopes.

### Migration Phase #3 — event-processor

| # | FQ class | FQ test | Status | Commit |
|---|---|---|---|---|
| 1 | … | … | pending | — |

### Migration Phase #4 — command-gateway

| # | FQ class | FQ test | Status | Commit |
|---|---|---|---|---|
| 1 | … | … | pending | — |

### Migration Phase #5 — query-gateway

| # | FQ class | FQ test | Status | Commit |
|---|---|---|---|---|
| 1 | … | … | pending | — |

### Migration Phase #6 — query-handler

| # | FQ class | FQ test | Status | Commit |
|---|---|---|---|---|
| 1 | … | … | pending | — |

### Migration Phase #7 — interceptors

| # | FQ class | FQ test | Status | Commit |
|---|---|---|---|---|
| 1 | … | … | pending | — |

### Migration Phase #8 — event-storage-engine + configuration sweep

> Phase #8 bundles two related concerns into one pass:
> 1. **Storage-engine bean swap** (one-shot) — JPA / Axon Server engine, see below.
> 2. **Configuration classes** (iterative) — any class reading `eventStore()` / `eventBus()` OR declaring generic writes (`@Bean ConfigurerModule` for non-Axon components, `DefaultConfigurer.defaultConfiguration()`, free-standing lifecycle hooks, `Lifecycle` interface). Migrated via [event-storage-engine/configuration.md](../references/event-storage-engine/configuration.md). Topic-specific configuration is handled by its topic recipe: event-processor reads / wiring in #3 (see also [event-processor/configuration-reads.md](../references/event-processor/configuration-reads.md)), command-gateway reads in #4 ([command-gateway/configuration-reads.md](../references/command-gateway/configuration-reads.md)), query-gateway reads in #5 ([query-gateway/configuration-reads.md](../references/query-gateway/configuration-reads.md)), aggregate registration in #2.

**Configuration-class items**

| # | FQ class | FQ test | Status | Commit |
|---|---|---|---|---|
| 1 | … | … | pending | — |

**Storage-engine bean swap**

- **Path chosen:** _A (Spring Boot) / B (framework-config)_
- **Sub-path:** _JPA / Axon Server_
- **Evidence:** _AF4 beans observed + dependencies_
- **Configuration class touched:** _FQ class — bean(s) replaced_
- **Schema change required (out-of-band, user-owned):** _yes (JPA sub-path) / no (Axon Server)_
- **Commit:** `<short-sha>` — `feat(af5-migration): wire AggregateBased…EventStorageEngine`

> SQL / DDL / data migration is out of scope. Recipe never emits SQL.
> When a schema change is required, record the requirement here (and
> in `learnings.md`); user runs DDL out-of-band on their own database
> before stabilization runtime checks.

### Stabilization

- **Pre-flight (user has applied required AF5 schema change out-of-band, JPA sub-path):** _yes / no / n/a_
- **`./mvnw clean verify` first run:** _PASS / FAIL — module(s) failing_
- **Outstanding compile errors:**
  - `<FQ class>` — `<one-line cause>` — `pending` / `fix in <sha>`
- **Outstanding test failures:**
  - `<FQ test method>` — `<one-line cause>` — `pending` / `fix in <sha>`
- **Deferred items folded forward:** _list_
- **Behavior changes confirmed by user:** _list_
