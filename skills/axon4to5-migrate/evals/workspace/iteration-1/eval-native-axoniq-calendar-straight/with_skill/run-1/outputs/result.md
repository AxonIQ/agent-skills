**Result:** ✅ Success
**Source:** `com.dddheroes.heroesofddd.calendar.write.Calendar`
**Recipe:** axon4to5-aggregate

**Notes:** Path B (native configurer) migration applied. `@Aggregate` replaced with `@EventSourcedEntity(tagKey = "Calendar", idType = CalendarId.class)` from `org.axonframework.eventsourcing.annotation` (framework annotation, not the Spring `@EventSourced` stereotype). `@AggregateIdentifier` and `@CreationPolicy(CREATE_IF_MISSING)` removed; the latter maps to AF5 instance `@CommandHandler` on a no-arg `@EntityCreator` (default post-migration shape). Every `@CommandHandler` now takes an `EventAppender` parameter, and `AggregateLifecycle.apply(...)` was rewritten to `eventAppender.append(...)`. AF4 imports dropped; AF5 imports added with the correct `.messaging.` / `.annotation.` / `.reflection.` infixes.

**Learnings:**
- Configurer wiring file (Path B registration) not present in the single-file scope of this `mode=single` invocation — caller owns the `EventSourcedEntityModule.autodetected(CalendarId.class, Calendar.class)` registration on `EventSourcingConfigurer` outside this run.
