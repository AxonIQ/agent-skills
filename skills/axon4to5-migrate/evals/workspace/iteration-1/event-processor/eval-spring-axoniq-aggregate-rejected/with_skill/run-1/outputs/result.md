**Result:** ⏭️ Rejected
**Source:** `com.dddheroes.heroesofddd.calendar.write.Calendar`
**Recipe:** axon4to5-event-processor

**Notes:** Applicable predicate 2 — `@Aggregate` + `@EventSourcingHandler` — failed at `Calendar.java:18` (class annotated `@Aggregate`) with `@EventSourcingHandler` method at `Calendar.java:43`. This is an event-sourced aggregate, not an event-processor. Route to the aggregate recipe (`axon4to5-aggregate`). No edits made to `Calendar.java`; source remains byte-identical (no `@Namespace`, no AF5 `@EventHandler` import, no `@EntityCreator` added).
