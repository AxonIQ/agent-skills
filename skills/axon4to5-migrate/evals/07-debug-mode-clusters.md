# Scenario 07 — DEBUG mode clusters errors before routing

## Starting state

- OpenRewrite (Migration Phase #1) ran. Pinned decisions in place. No `isolated-*` scope active.
- Full project compile is RED with ~40 errors. Of those:
  - 15 are `cannot find symbol: method apply(...)` — every `AggregateLifecycle.apply` call.
  - 10 are `cannot find symbol: class AggregateTestFixture` — every test class.
  - 15 are cascading errors from the above (downstream call sites that used the return type).

## User input

```
/axon4to5-migrate debug
```

## Expected behavior

1. Mode: DEBUG.
2. `./mvnw test-compile -DskipTests …` runs. 40 diagnostics captured.
3. Diagnostics are normalized (file:line, error kind, symbol, primary vs cascade).
4. Clustering produces ~2 clusters: `aggregate` (one per aggregate class), NOT 15 message-shaped buckets.
5. Highest-leverage cluster (the aggregate that owns the most cascading errors) is picked. ONE recipe call: `aggregate` against that class.
6. After the recipe commits, the loop restarts: re-compile, re-cluster from fresh evidence. NOT a linear scan of every original error.

## Pass / fail signals

- ✅ Pass: ≤ 2 recipe invocations per outer loop pass; cluster size dominated by aggregate count, not message count.
- ❌ Fail: orchestrator runs `aggregate` 15 times in a row because it treats each `apply(...)` error as its own item. Or runs `mvn` between every recipe call without re-clustering.

## Why this matters

Linear-fix mode wastes context and serializes naturally-batched work. Root-cause clustering is the only way debug stays tractable on a project with hundreds of errors after OpenRewrite.
