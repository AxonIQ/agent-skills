# 08 — Rejected: aggregate source routed to the event-processor recipe

**Why this case is interesting:** The event-processor recipe must reject sources that are not event-handling components. Aggregates carry `@EventSourcingHandler` (NOT `@EventHandler`), and the recipe must not be tricked by the partial similarity into editing the aggregate. The rejection NOTES point the caller to the aggregate recipe so the queue can route correctly.

**Apply-condition:** `$SOURCE` is annotated `@Aggregate` / `@AggregateRoot` with `@EventSourcingHandler` methods.

## Detection

The `# Applicable` decision rule, predicate 2:

> Aggregate — class annotated `@Aggregate` / `@AggregateRoot` AND has at least one `@EventSourcingHandler` (not `@EventHandler`). → **Rejected** with NOTES naming `aggregate`.

Detection reads the class header annotation + scans methods for `@EventSourcingHandler` (the AF4 import is `org.axonframework.eventsourcing.EventSourcingHandler`; AF5 is `org.axonframework.eventsourcing.annotation.EventSourcingHandler`). Either form triggers predicate 2.

## Source (left untouched)

```java
package com.dddheroes.heroesofddd.calendar.write;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
class Calendar {

    @AggregateIdentifier
    private CalendarId calendarId;

    @CommandHandler
    void decide(StartDay command) {
        apply(new DayStarted(command.calendarId(), command.day()));
    }

    @EventSourcingHandler
    void evolve(DayStarted event) {
        this.calendarId = new CalendarId(event.calendarId());
    }

    Calendar() { }
}
```

## Result block

```
return REJECTED

> **Result:** ⏭️ Rejected
> **Source:** `com.dddheroes.heroesofddd.calendar.write.Calendar`
> **Recipe:** axon4to5-event-processor
>
> **Notes:** Applicable predicate 2 failed at `Calendar.java:11` — class is annotated `@Aggregate` and has `@EventSourcingHandler` methods (event-sourced aggregate). This is the aggregate recipe's job. Route to `axon4to5-aggregate`.
```

## What did NOT happen

- No edits to `Calendar.java`. The event-processor recipe ran the `# Applicable` check, predicate 2 returned a definitive "no", and the recipe exited before Research.
- No `# Scope` enumeration, no `# References` reading, no `# Success Criteria` evaluation. Rejected halts the sub-flow at the first diamond in FLOW.md.
- No `@Namespace` added, no `@EventHandler` import introduced. (Critical guardrail — adding `@Namespace` to an aggregate would compile but mis-route command handling at runtime.)
- No retry budget consumed (Rejected is not a Failure).

## Other Rejected predicates (recap)

The `# Applicable` decision rule lists six predicates:

1. **Saga** — `@Saga` OR `@SagaEventHandler`. Route to saga recipe.
2. **Aggregate** — `@Aggregate` / `@AggregateRoot` + `@EventSourcingHandler`. Route to aggregate recipe. *(This use case.)*
3. **Event-handling component, AF4 shape** — `@EventHandler` AND `@ProcessingGroup`. **Continue** to Research.
4. **Event-handling component, partially-migrated** — `@EventHandler` AND `@Namespace`. **Continue** (Success Criteria pre-Apply check decides).
5. **Event-handling component, no group/namespace** — `@EventHandler` but no group marker. **Continue** with NOTES surfacing the missing namespace.
6. **None of the above** — no `@EventHandler` anywhere. Rejected with NOTES naming the failed predicate.

## Caveats

- **`@EventSourcingHandler` vs `@EventHandler` is the load-bearing distinction.** Both are method-level annotations on what looks like event-handling code; the difference is which framework subsystem schedules them. Aggregates use `@EventSourcingHandler` (re-applying past events to reconstruct state); event processors use `@EventHandler` (downstream event reactions). Mis-routing breaks command handling silently.
- **NOTES must say `aggregate` or name the aggregate recipe explicitly.** Without specificity, the orchestrator's queue cannot route to the right next recipe in project mode.
- **Source on disk MUST be byte-identical to the input.** The grader can sanity-check this by asserting `@Aggregate` is still present and `@EventSourced` / `@Namespace` / `@EventHandler` (AF5 import) were NOT added.
- **State-stored aggregates also fall here.** An `@Aggregate` + JPA `@Entity` source with zero `@EventSourcingHandler` methods technically misses predicate 2 (no `@EventSourcingHandler`); the aggregate recipe rejects it as state-stored. The event-processor recipe doesn't see it at all — predicate 6 catches it as "none of the above".
