package com.example.calendar.write;

// Realistic post-OpenRewrite-Phase-1 partial state for configuration=spring:
// - @Aggregate (Spring stereotype) was mechanically swapped to @EventSourced
// - …but tagKey / idType attributes were NOT added (defaults relied on)
// - @AggregateIdentifier annotation + import STILL present
// - @CreationPolicy(CREATE_IF_MISSING) annotation STILL present
// - @CommandHandler / @EventSourcingHandler imports are STILL the AF4 packages
// - AggregateLifecycle.apply(...) is STILL in handler bodies (no EventAppender threading)
// - No @EntityCreator on the no-arg constructor
// - Imports are a MIX of AF5 (the new @EventSourced) + AF4 (everything else)

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.extension.spring.stereotype.EventSourced;
import org.axonframework.modelling.command.AggregateCreationPolicy;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.CreationPolicy;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@EventSourced
class PartialCalendarSpring {

    @AggregateIdentifier
    private CalendarId calendarId;
    private int currentDay;

    @CommandHandler
    @CreationPolicy(AggregateCreationPolicy.CREATE_IF_MISSING)
    void decide(StartDay command) {
        apply(new DayStarted(command.calendarId(), command.day()));
    }

    @EventSourcingHandler
    void evolve(DayStarted event) {
        this.calendarId = new CalendarId(event.calendarId());
        this.currentDay = event.day();
    }

    @CommandHandler
    void decide(FinishDay command) {
        if (currentDay != command.day()) throw new IllegalStateException("not current day");
        apply(new DayFinished(command.calendarId(), command.day()));
    }

    @EventSourcingHandler
    void evolve(DayFinished event) {
        // currentDay stays; new StartDay command will increment
    }

    PartialCalendarSpring() {
        // required by Axon — no @EntityCreator yet
    }

    public record CalendarId(String value) { }
    public record StartDay(String calendarId, int day) { }
    public record FinishDay(String calendarId, int day) { }
    public record DayStarted(String calendarId, int day) { }
    public record DayFinished(String calendarId, int day) { }
}
