# Recipe `aggregate` — blockers

Run every Detection grep below BEFORE `## Procedure`. For each hit: run the `AskUserQuestion`, record the answer under `decisions.<key>`, apply "Effect". Never silently rewrite around an unresolved blocker.

> 🚨 **DATA MIGRATION IS NOT IN SCOPE.** Dropping `snapshotTriggerDefinition` only removes the **code config**; existing snapshot rows are not touched. User owns data cleanup out-of-band.

## B1 — `snapshotTriggerDefinition` / `Snapshotter` / `SnapshotTriggerDefinition`

**Why.** `@EventSourcedEntity` does not expose a finalized snapshot API yet. AF4 trigger types have no AF5 rename target.

**Detection:**
```bash
grep -RnE 'snapshotTriggerDefinition|Snapshotter|SnapshotTriggerDefinition' --include='*.java' --include='*.kt' <aggregate file> <aggregate package>
```

Also inspect the `@Aggregate` annotation directly for `snapshotTriggerDefinition = "..."`.

> ⚠️ **Detection-after-OpenRewrite caveat.** The bulk recipe silently strips `snapshotTriggerDefinition` and leaves a `// TODO #LLM: reconfigure snapshot trigger` marker. Add secondary probes:
> ```bash
> grep -RnE 'TODO[^\n]*snapshot' --include='*.java' --include='*.kt' <aggregate file> <aggregate package>
> git log -p -- <aggregate file> | grep -E 'snapshotTriggerDefinition'
> ```
> **Recommended:** run primary detection BEFORE bulk OpenRewrite, pin the decision in `progress.md` as `snapshotting (<AggregateSimpleName>): <accept-drop|pause-migration|remove-feature-first>`. Per-aggregate Preflight reads the pinned value and skips the prompt.

**AskUserQuestion:**
- `accept-drop` — user accepts no snapshotting until AF5 ships the API.
- `pause-migration` — user removes/relocates snapshot config first.
- `remove-feature-first` — user deletes snapshot config now, re-introduces later.

**Output key:** `snapshotting: none | accept-drop | pause-migration | remove-feature-first`.

**Effect:**
- `accept-drop` → proceed; do NOT carry `snapshotTriggerDefinition` to `@EventSourced`.
- others → `result: blocked`, `next: record-and-skip`, exit.

Caching attributes on `@Aggregate` fold into this same decision.

## B3 — Map-typed `@AggregateMember`

**Why.** `Map<K, V>`-typed `@AggregateMember` is a breaking change — `@EntityMember` doesn't support the same shape. Auto-rewrite silently re-keys the collection.

**Detection:**
```bash
grep -RnE '@AggregateMember[\s\S]{0,200}Map<' --include='*.java' --include='*.kt' <aggregate file>
```

**AskUserQuestion:**
- `surface-and-defer` *(Recommended)* — emit Output noting Map-typed member; user redesigns to `List`/`Set` first.
- `pause-migration` — user redesigns now.

**Output key:** `map-typed-aggregate-member: none | surface-and-defer | pause-migration`.

**Effect:** Either path → `result: blocked`, `next: record-and-skip`, exit. No edits.

## B4 — `SagaTestFixture` on the aggregate's test class

**Why.** No AF5 replacement for `SagaTestFixture`.

**Detection:**
```bash
grep -RnE 'SagaTestFixture' --include='*.java' --include='*.kt' <test class>
```

**AskUserQuestion:**
- `surface-and-skip-test` *(Recommended)* — leave saga test on AF4; skip T.1–T.5 for this test class.
- `pause-migration` — stop.

**Output key:** `saga-test-fixture-flagged: none | surface-and-skip-test | pause-migration`.

## B5 — `@DeadlineHandler` / `DeadlineManager` use inside the aggregate

**Why.** AF5 has **no direct successor** to `DeadlineManager`, `@DeadlineHandler`, `DeadlineMessage`, or the four AF4 impls (`Simple`/`JobRunr`/`Quartz`/`DbScheduler`). Naive rewrite drops scheduling silently — the missed deadline turns into a runtime business-logic failure.

**Detection:**
```bash
grep -RnE '@DeadlineHandler|DeadlineManager|DeadlineMessage|deadlineManager\.schedule|cancelSchedule|cancelAllWithinScope' --include='*.java' --include='*.kt' <aggregate file> <aggregate package>
```

Also inspect injected fields / constructor params for `DeadlineManager`.

**AskUserQuestion:**
- `accept-stays-af4` — deadline code stays AF4; aggregate slice won't compile under AF5 deps until AF5 ships a replacement or user removes/redesigns. Surface the kept-AF4 surface in Output `notes`.
- `pause-migration` *(Recommended)* — user removes/replaces the deadline flow first (own `ScheduledExecutorService` + JPA timestamp poll, or contact Axoniq for workflow roadmap).
- `remove-feature-first` — user redesigns now; recipe exits, resumes after cleanup commit.

**Output key:** `deadline-handler: none | accept-stays-af4 | pause-migration | remove-feature-first`.

**Effect:**
- `accept-stays-af4` → proceed with Steps 3–14 + variant addenda + Path A/B; do NOT touch `@DeadlineHandler` methods or `DeadlineManager` injection. Surface the AF4 surface in Output `notes`.
- others → `result: blocked`, `next: record-and-skip`, exit.

> A standalone `@Bean DeadlineManager` on a `@Configuration` class is the same blocker. Comment out + `TODO[AF5 migration: B5]`, never silently delete. The mechanical rewrite for the bean form belongs to the event-storage-engine recipe's Step W.
