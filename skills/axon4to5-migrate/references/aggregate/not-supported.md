# Recipe `aggregate` — not-supported / blockers

**Read this file BEFORE running `## Procedure`.** Each blocker below has a Detection grep and an `AskUserQuestion` flow. The aggregate recipe must NOT silently rewrite around an unresolved blocker — wrong shape compiles cleanly and only fails at test time, so user input is required where AF5 has no portable target.

> 🚨 **DATA MIGRATION IS NOT IN SCOPE.** This skill rewrites **code only** (annotations, imports, handler shapes, test fixture). It does NOT migrate snapshots, event-store rows, or any other persisted aggregate state. Dropping `snapshotTriggerDefinition` only removes the **code config** — existing snapshot rows in storage are not deleted, rewritten, or re-read by this skill. Cleanup of stale snapshot data is the user's responsibility, out-of-band.

## How to use

1. Run every Detection grep below against the candidate aggregate class, its events, child entities, and the configuration referencing it.
2. For each blocker that fires:
   - Run the `AskUserQuestion` exactly as written.
   - Record the user's pick under Output `decisions.<key>`.
   - Apply "Effect on Procedure".
3. Only when every fired blocker has a recorded outcome → proceed to `## Procedure`.

## Blockers

### B1 — `snapshotTriggerDefinition` / `Snapshotter` / `SnapshotTriggerDefinition`

**Why blocker.** AF5's `@EventSourcedEntity` does not yet expose a finalized snapshot API. The `snapshotTriggerDefinition` attribute does NOT exist on `@EventSourced` — silently dropped during a naive rewrite. AF4 trigger types (`EventCountSnapshotTriggerDefinition`, `SpringAggregateSnapshotterFactoryBean`) have no AF5 rename target.

**Detection.**

```bash
grep -RnE 'snapshotTriggerDefinition|Snapshotter|SnapshotTriggerDefinition' \
     --include='*.java' --include='*.kt' <aggregate file> <aggregate package>
```

Also inspect the `@Aggregate` annotation directly — if it carries `snapshotTriggerDefinition = "..."`, this blocker fires.

> ⚠️ **Detection-after-OpenRewrite caveat.** If the OpenRewrite bulk
> recipes (`UpgradeAxon4ToAxon5` / `UpgradeAxon4ToAxoniq5`) have already
> run on this codebase, they will have silently stripped
> `snapshotTriggerDefinition` from `@Aggregate` and left a
> `// TODO #LLM: reconfigure snapshot trigger (AF4 had snapshotTriggerDefinition = "...")`
> comment in its place. The primary grep above will no longer fire on
> sources that have already been bulk-rewritten. Add these secondary
> probes:
>
> ```bash
> # Leftover OpenRewrite TODO marker
> grep -RnE 'TODO[^\n]*snapshot' --include='*.java' --include='*.kt' \
>      <aggregate file> <aggregate package>
>
> # Pre-OpenRewrite history — confirm whether the aggregate ever had it
> git log -p -- <aggregate file> | grep -E 'snapshotTriggerDefinition'
> ```
>
> Recommended: run the **primary detection BEFORE** the bulk OpenRewrite
> recipes touch the source (so the original `@Aggregate(snapshotTriggerDefinition = ...)`
> is still present), and pin the resulting decision in `progress.md`
> Pinned-decisions as
> `snapshotting (<AggregateSimpleName>): <accept-drop | pause-migration | remove-feature-first>`.
> Per-aggregate Preflight then reads the pinned value and skips the
> AskUserQuestion when already decided.

**AskUserQuestion — choose one:**

- `accept-drop` — drop the attribute; user accepts no snapshotting until AF5 ships the API.
- `pause-migration` — stop; user removes/relocates snapshot config first.
- `remove-feature-first` — user deletes snapshot config now and will re-introduce later when AF5 has the API.

**Output decision key.** `snapshotting: <none | accept-drop | pause-migration | remove-feature-first>`

**Effect on Procedure.**
- `accept-drop` → proceed; do NOT carry `snapshotTriggerDefinition` over to `@EventSourced`.
- `pause-migration` → emit Output with `result: blocked`, `caller-expects.next: record-and-skip`, exit.
- `remove-feature-first` → emit Output with `result: blocked`, `caller-expects.next: record-and-skip`, exit; user will return after the cleanup commit.

Same surfacing applies to any `Snapshotter` / `SnapshotTriggerDefinition` reference reachable from this aggregate. Caching attributes on `@Aggregate` are similarly not portable — fold into this decision.

### B3 — Map-typed `@AggregateMember` (multi-entity breaking change)

**Why blocker.** `Map<K, V>`-typed `@AggregateMember` collections are a breaking change in AF5 — `@EntityMember` does not support the same Map shape. Auto-rewriting silently re-keys the collection; safer to surface.

**Detection.**

```bash
grep -RnE '@AggregateMember[\s\S]{0,200}Map<' \
     --include='*.java' --include='*.kt' <aggregate file>
```

**AskUserQuestion — choose one:**

- `surface-and-defer` *(Recommended)* — emit Output noting Map-typed member; user redesigns to `List` / `Set` first, then re-runs recipe.
- `pause-migration` — stop; user redesigns now.

**Output decision key.** `map-typed-aggregate-member: <none | surface-and-defer | pause-migration>`

**Effect on Procedure.** Either path → emit Output with `result: blocked`, `caller-expects.next: record-and-skip`, exit. No edits.

### B4 — `SagaTestFixture` on the aggregate's test class

**Why blocker.** `SagaTestFixture` has no AF5 replacement. Surfacing prevents silent rewrites of saga tests using the aggregate's primary test path.

**Detection.**

```bash
grep -RnE 'SagaTestFixture' \
     --include='*.java' --include='*.kt' <test class>
```

**AskUserQuestion — choose one:**

- `surface-and-skip-test` *(Recommended)* — leave the saga test on AF4 deps; record skip; recipe migrates the aggregate but not this test.
- `pause-migration` — stop.

**Output decision key.** `saga-test-fixture-flagged: <none | surface-and-skip-test | pause-migration>`

**Effect on Procedure.**
- `surface-and-skip-test` → run aggregate steps; skip T.1–T.5 for this test class.
- `pause-migration` → emit Output with `result: blocked`, `caller-expects.next: record-and-skip`, exit.

### B5 — `@DeadlineHandler` / `DeadlineManager` use inside the aggregate

**Why blocker.** AF4 lets aggregates schedule deadlines via `DeadlineManager.schedule(...)` and react via `@DeadlineHandler` methods on the aggregate (Scope = the aggregate instance). AF5 has **no direct successor** — `DeadlineManager`, `@DeadlineHandler`, `DeadlineMessage`, and the four AF4 implementations (`SimpleDeadlineManager`, `JobRunrDeadlineManager`, `QuartzDeadlineManager`, `DbSchedulerDeadlineManager`) are gone. A naive rewrite would silently drop scheduling/cancellation; the missed deadline turns into a runtime business-logic failure (e.g. an unpaid order that never expires).

**Detection.**

```bash
# Aggregate file + its package
grep -RnE '@DeadlineHandler|DeadlineManager|DeadlineMessage|deadlineManager\.schedule|cancelSchedule|cancelAllWithinScope' \
     --include='*.java' --include='*.kt' <aggregate file> <aggregate package>
```

Also inspect injected fields on the aggregate / its constructor parameters for `DeadlineManager` (rare but legal in AF4).

**AskUserQuestion — choose one:**

- `accept-stays-af4` — deadline code stays AF4; the aggregate slice will not compile under AF5 deps until either AF5 ships a deadline replacement or the user removes/redesigns the deadline flow.
- `pause-migration` *(Recommended)* — stop; user removes/replaces the deadline-driven flow first (e.g. plain `ScheduledExecutorService` + JPA timestamp-poll, like the framework-config bike-rental reference), or contacts Axoniq for the workflow roadmap.
- `remove-feature-first` — user accepts they will redesign the deadline-driven part now; recipe exits and resumes after the cleanup commit.

**Output decision key.** `deadline-handler: <none | accept-stays-af4 | pause-migration | remove-feature-first>`

**Effect on Procedure.**
- `accept-stays-af4` → proceed with annotation rewrites Steps 3–14 + variant addenda + Path A or Path B; do NOT touch `@DeadlineHandler` methods or `DeadlineManager` injection sites; surface the kept-AF4 surface in Output `notes`. The aggregate slice will need a follow-up commit (or stays on AF4 deps) before stabilization can go green.
- `pause-migration` / `remove-feature-first` → emit Output with `result: blocked`, `caller-expects.next: record-and-skip`, exit. No edits.

> Same surfacing applies to any `DeadlineManager` reference reachable from this aggregate (constructor parameter, helper class, scheduler bean injected via the aggregate). The Quartz / JobRunr / DbScheduler implementation classes (`*DeadlineManager`) bring AF4 transitive deps that won't resolve on AF5; flag them as part of `accept-stays-af4`.

> **Bootstrap-layer occurrence (outside any aggregate).** A standalone `@Bean DeadlineManager` declared on a `@SpringBootApplication` / `@Configuration` class (rather than used from inside the aggregate) is the same blocker — same pinned decision, same disposition. The mechanical rewrite for the bean form (comment out + `TODO[AF5 migration]` marker citing this B5 key, retain wiring for the day AF5 ships the successor) lives in [../event-storage-engine/configuration.md](../event-storage-engine/configuration.md) §W.9. Never silently delete the bean — the comment block preserves the AF4 factory shape and links back here so reviewers can audit which feature has been parked.
