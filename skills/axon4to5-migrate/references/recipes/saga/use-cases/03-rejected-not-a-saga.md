# Use case 03 — Rejected: source is not a saga

**Why interesting:** shows the rejection path when the saga recipe is invoked on a class that is not a saga — typically an aggregate or projector accidentally routed here. Recipe must leave source untouched.

## Example

`$SOURCE` is `CreatureRecruitmentAggregate.java`, annotated `@Aggregate` with `@EventSourcingHandler` methods. The caller invoked the saga recipe by mistake.

## Expected outcome

```
return REJECTED

> **Result:** ⏭️ Rejected
> **Source:** `com.example.CreatureRecruitmentAggregate`
> **Recipe:** axon4to5-saga
>
> **Notes:** Applicable predicate failed — class is annotated @Aggregate with @EventSourcingHandler methods. This is an event-sourced aggregate, not a saga. Route to the aggregate recipe instead. No edits made.
```

## What did NOT happen

- No `@Component` added to the aggregate.
- No `@EventHandler` (AF5) import added.
- No state entity or repository created.
- Source file byte-identical to input.

## Routing guidance in NOTES

Always name the correct recipe when rejecting:
- `@Aggregate` + `@EventSourcingHandler` → route to **aggregate** recipe
- `@ProcessingGroup` + `@EventHandler` (projector) → route to **event-processor** recipe
- No recognizable Axon 4 marker at all → ask user to clarify
