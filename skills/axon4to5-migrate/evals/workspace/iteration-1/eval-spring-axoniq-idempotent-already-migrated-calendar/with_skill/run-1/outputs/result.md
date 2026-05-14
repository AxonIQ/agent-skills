**Result:** ✅ Success
**Source:** `com.dddheroes.heroesofddd.calendar.write.Calendar`
**Recipe:** axon4to5-aggregate

**Notes:** All Success Criteria match on first visit to FLOW.md S5 — pre-Apply check passes, recipe is idempotent. `edits=none (idempotent)`. Source already on AF5 shape: `@EventSourced(tagKey = "Calendar", idType = CalendarId.class)` (Path A — Spring stereotype from `org.axonframework.extension.spring.stereotype`), `@EntityCreator` on no-arg constructor, `EventAppender` threaded through every `@CommandHandler`, no AF4 imports survive. No edits applied.
