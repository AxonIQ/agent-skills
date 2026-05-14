**Result:** ✅ Success
**Source:** `com.dddheroes.heroesofddd.calendar.write.Calendar`
**Recipe:** axon4to5-aggregate

**Notes:** Path A (Spring Boot) migration applied to `Calendar.java` + `CalendarTest.java`. Aggregate now carries `@EventSourced(tagKey = "Calendar", idType = CalendarId.class)`; AF4 annotations/imports removed; `@EntityCreator` on no-arg constructor; both `@CommandHandler` methods take `EventAppender` and use `eventAppender.append(...)`. Test class migrated to `AxonTestFixture` with `EventSourcingConfigurer` + `EventSourcedEntityModule.autodetected(CalendarId.class, Calendar.class)`, fluent `given()/when()/then()` DSL, and `@AfterEach fixture.stop()` added.
