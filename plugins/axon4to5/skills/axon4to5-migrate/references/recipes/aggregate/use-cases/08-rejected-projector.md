# 08 — Rejected: projector source routed to the aggregate recipe

**Why this case is interesting:** The aggregate recipe must reject sources that are not aggregates, but the rejection must be informative — pointing the caller to the correct sister recipe. The source file MUST remain unchanged. This use case anchors what Rejected outputs look like.

**Apply-condition:** `$SOURCE` annotated `@ProcessingGroup` AND zero `@CommandHandler` methods.

## Detection

The `# Applicable` decision rule, predicate 2:

> Projector / event processor — class annotated `@ProcessingGroup` AND zero `@CommandHandler` methods.

Detected by reading the class header + scanning methods for `@CommandHandler`.

## Source (left untouched)

```java
package com.dddheroes.heroesofddd.creaturerecruitment.read;

import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.stereotype.Component;

@Component
@ProcessingGroup("ReadModel_Dwelling")
public class DwellingReadModelProjector {

    private final DwellingReadModelRepository repository;

    @EventHandler
    public void on(DwellingBuilt event) {
        repository.save(new DwellingReadModel(event.dwellingId(), event.creatureId()));
    }

    @EventHandler
    public void on(AvailableCreaturesChanged event) {
        repository.findById(event.dwellingId()).ifPresent(rm -> rm.setAvailable(event.changedTo()));
    }
}
```

## Result block

```
return REJECTED

> **Result:** ⏭️ Rejected
> **Source:** `com.dddheroes.heroesofddd.creaturerecruitment.read.DwellingReadModelProjector`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** Applicable predicate 2 failed at `DwellingReadModelProjector.java:9` — class is annotated `@ProcessingGroup("ReadModel_Dwelling")` with zero `@CommandHandler` methods (`@EventHandler` only). This is a projection / event-handling component, not an aggregate. Route to the `event-processor` recipe — the aggregate recipe does not touch projector sources.
```

## What did NOT happen

- No edits to the source file. The aggregate recipe ran the `# Applicable` check, predicate 2 returned a definitive "no", and the recipe exited before Research.
- No `# Scope` enumeration, no `# References` reading, no `# Success Criteria` evaluation. Rejected halts the sub-flow at the first diamond in FLOW.md.
- No retry budget consumed (Rejected is not a Failure).

## Other Rejected predicates

The `# Applicable` decision rule lists six predicates that result in Rejected (or continuation):

1. **Saga** — `@Saga` OR `@SagaEventHandler` / `@StartSaga` / `@EndSaga`. Route to saga recipe.
2. **Projector / event processor** — `@ProcessingGroup` AND zero `@CommandHandler`. Route to event-processor recipe. *(This use case.)*
3. **State-stored aggregate** — `@Aggregate` AND JPA `@Entity` AND zero `@EventSourcingHandler` AND direct field mutation in command handlers. State-stored support is out of scope of this skill.
4. **Event-sourced aggregate, AF4 shape** — `@Aggregate` / `@AggregateRoot` AND ≥1 `@EventSourcingHandler`. **Continue** to Research.
5. **Event-sourced aggregate, partially-migrated** — already on `@EventSourced` / `@EventSourcedEntity` AND ≥1 `@EventSourcingHandler`. **Continue** — the pre-Apply Success Criteria check decides idempotent-Success vs. continue.
6. **None of the above** — Rejected with NOTES naming the failed predicate.

## Caveats

- **NOTES must name the predicate** that failed, not just "not an aggregate". Without specificity, the caller cannot route to the right next recipe. (Predicate 1 → saga recipe; predicate 2 → event-processor recipe; predicate 3 → no successor — surface as project-level concern.)
- **Source on disk MUST be byte-identical** to the input. The grader uses this as a sanity check that Rejected really did not touch the file (e.g. by asserting `@ProcessingGroup` is still present and `@EventSourced` / `@EventSourcedEntity` / `@EntityCreator` were NOT added).
- **Do not "pre-emptively" migrate any imports** even if a Rejected source happens to have AF4 imports that look migratable. Rejected means "wrong recipe" — the right recipe will own those edits.
- Dual-role classes (BOTH `@QueryHandler` AND `@EventHandler` on the same class) also fail predicate 2 from this recipe's perspective and are Rejected. The event-processor / query-handler recipes own them.
