# 01 — Spring Boot, straight migration (Path A)

**Why this case is interesting:** Baseline Path A. `@Aggregate` → `@EventSourced`, `apply(...)` → `eventAppender.append(...)`, no-arg `@EntityCreator`, every event gets `@EventTag`. The shape every other use case extends from.

**Apply-condition:** `configuration=spring` AND no `@AggregateMember` AND no polymorphism AND no `snapshotTriggerDefinition`.

## Before (AF4)

```java
package com.dddheroes.heroesofddd.calendar.write;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateCreationPolicy;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.CreationPolicy;
import org.axonframework.spring.stereotype.Aggregate;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
class Calendar {

    @AggregateIdentifier
    private CalendarId calendarId;
    private Month currentMonth;
    private Week currentWeek;
    private Day currentDay;

    @CommandHandler
    @CreationPolicy(AggregateCreationPolicy.CREATE_IF_MISSING)
    void decide(StartDay command) {
        new CannotSkipDays(command, currentMonth, currentWeek, currentDay).verify();
        apply(DayStarted.event(command.calendarId(), command.month(), command.week(), command.day()));
    }

    @EventSourcingHandler
    void evolve(DayStarted event) {
        calendarId = new CalendarId(event.calendarId());
        currentMonth = new Month(event.month());
        currentWeek = new Week(event.week());
        currentDay = new Day(event.day());
    }

    @CommandHandler
    void decide(FinishDay command) {
        new CanOnlyFinishCurrentDay(command, currentMonth, currentWeek, currentDay).verify();
        apply(DayFinished.event(command.calendarId(), command.month(), command.week(), command.day()));
    }

    Calendar() { /* required by Axon */ }
}
```

## After (AF5)

```java
package com.dddheroes.heroesofddd.calendar.write;

import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.extension.spring.stereotype.EventSourced;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@EventSourced(tagKey = "Calendar", idType = CalendarId.class)
class Calendar {

    private CalendarId calendarId;
    private Month currentMonth;
    private Week currentWeek;
    private Day currentDay;

    @CommandHandler
    void decide(StartDay command, EventAppender eventAppender) {
        new CannotSkipDays(command, currentMonth, currentWeek, currentDay).verify();
        eventAppender.append(DayStarted.event(command.calendarId(), command.month(), command.week(), command.day()));
    }

    @EventSourcingHandler
    void evolve(DayStarted event) {
        calendarId = new CalendarId(event.calendarId());
        currentMonth = new Month(event.month());
        currentWeek = new Week(event.week());
        currentDay = new Day(event.day());
    }

    @CommandHandler
    void decide(FinishDay command, EventAppender eventAppender) {
        new CanOnlyFinishCurrentDay(command, currentMonth, currentWeek, currentDay).verify();
        eventAppender.append(DayFinished.event(command.calendarId(), command.month(), command.week(), command.day()));
    }

    @EntityCreator
    Calendar() { /* required by Axon */ }
}
```

Plus on every event class:

```java
import org.axonframework.eventsourcing.annotation.EventTag;
import org.axonframework.messaging.eventhandling.annotation.Event;

@Event
public record DayStarted(@EventTag(key = "Calendar") String calendarId, int month, int week, int day) { }
```

Plus on every command class:

```java
import org.axonframework.modelling.annotation.TargetEntityId;
import org.axonframework.messaging.commandhandling.annotation.Command;

@Command
public record FinishDay(@TargetEntityId String calendarId, int month, int week, int day) { }
```

## What changed

- `@Aggregate` (`org.axonframework.spring.stereotype.Aggregate`) → `@EventSourced(tagKey = "Calendar", idType = CalendarId.class)` (`org.axonframework.extension.spring.stereotype.EventSourced` — the `.extension.spring.` infix is mandatory).
- `tagKey` AND `idType` always emitted explicitly. Defaults exist but invisible defaults break on rename.
- `@AggregateIdentifier` annotation + import removed. Field stays plain.
- `@CreationPolicy(CREATE_IF_MISSING)` removed — instance `@CommandHandler` + no-arg `@EntityCreator` is the default semantics in AF5. (See [aggregates/index.adoc](../../../docs/paths/aggregates/index.adoc) § Removal of `@CreationPolicy`.)
- `@CommandHandler` import → `org.axonframework.messaging.commandhandling.annotation.CommandHandler` (`.messaging.` infix mandatory).
- `@EventSourcingHandler` import → `org.axonframework.eventsourcing.annotation.EventSourcingHandler` (`.annotation.` infix).
- `@EntityCreator` annotation on the no-arg constructor (`org.axonframework.eventsourcing.annotation.reflection.EntityCreator` — `.reflection.` infix mandatory).
- `AggregateLifecycle.apply(event)` → `eventAppender.append(event)` for each handler; `EventAppender eventAppender` parameter added on every `@CommandHandler` (`org.axonframework.messaging.eventhandling.gateway.EventAppender` — `.messaging.` infix).
- Every event gets `@EventTag(key = "Calendar")` on the id field; class-level `@Event`. One tag per event (no DCB).
- Every command gets `@Command`; `@TargetAggregateIdentifier` → `@TargetEntityId`.

## Caveats

- `tagKey` must be the **same string** on the entity and on every event. Pick the entity simple class name as the project default (`"Calendar"`), not the field name (`"calendarId"`).
- `idType` is non-default here (`CalendarId`, not `String`). Omitting it would fail silently at runtime, not at compile time.
- If the AF4 source had `@Aggregate(snapshotTriggerDefinition = "...")`, this use case's apply-condition doesn't match — the recipe emits Blocker B1 instead. See [04-snapshot-blocker.md](04-snapshot-blocker.md).
- Drop the AF4 framework-only no-arg constructor if `@EntityCreator` is on a new one; do not leave both.
