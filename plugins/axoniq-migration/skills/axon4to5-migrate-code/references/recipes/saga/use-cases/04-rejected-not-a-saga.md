# Use case 04 - Rejected: source is not a saga

**Why interesting:** shows the rejection path when the saga recipe is invoked on a class that is not a saga - typically
an aggregate or projector accidentally routed here. Recipe must leave source untouched.

## Example

`$SOURCE` is `CreatureRecruitmentAggregate.java`, annotated `@Aggregate` with `@EventSourcingHandler` methods. The
caller invoked the saga recipe by mistake.

## Expected outcome

```
return REJECTED

> **Result:** ⏭️ Rejected
> **Source:** `com.example.CreatureRecruitmentAggregate`
> **Recipe:** axon4to5-saga
>
> **Notes:** Applicable predicate 1 failed - class is annotated @Aggregate with @EventSourcingHandler methods. This is an event-sourced aggregate, not a saga. Route to the aggregate recipe instead. No edits made.
```

## What did NOT happen

- No `axon-legacy` dependency added to the build file.
- No `SagaLifecycle` / `CommandDispatcher` parameters introduced.
- No `@ProcessingGroup` -> `@Namespace` rewrite.
- Source file byte-identical to input.

## Routing guidance in NOTES

Always name the correct recipe when rejecting:

| Observed on `$SOURCE` | Route to |
|---|---|
| `@Aggregate` + `@EventSourcingHandler` | **aggregate** recipe |
| `@ProcessingGroup` / `@Namespace` + `@EventHandler`, no `@SagaEventHandler` | **event-processor** recipe |
| No recognizable Axon 4 marker at all | ask the user to clarify |

A class carrying **both** `@EventHandler` and `@SagaEventHandler` is a saga - predicate 3 wins, and the saga recipe
owns the whole class. Do not split it.
