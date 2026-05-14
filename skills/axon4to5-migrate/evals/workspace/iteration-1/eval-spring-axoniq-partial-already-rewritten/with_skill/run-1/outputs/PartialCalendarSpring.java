package com.example.calendar.write;

import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.extension.spring.stereotype.EventSourced;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@EventSourced(tagKey = "PartialCalendarSpring", idType = CalendarId.class)
class PartialCalendarSpring {

    private CalendarId calendarId;
    private int currentDay;

    @CommandHandler
    void decide(StartDay command, EventAppender eventAppender) {
        eventAppender.append(new DayStarted(command.calendarId(), command.day()));
    }

    @EventSourcingHandler
    void evolve(DayStarted event) {
        this.calendarId = new CalendarId(event.calendarId());
        this.currentDay = event.day();
    }

    @CommandHandler
    void decide(FinishDay command, EventAppender eventAppender) {
        if (currentDay != command.day()) throw new IllegalStateException("not current day");
        eventAppender.append(new DayFinished(command.calendarId(), command.day()));
    }

    @EventSourcingHandler
    void evolve(DayFinished event) {
        // currentDay stays; new StartDay command will increment
    }

    @EntityCreator
    PartialCalendarSpring() {
        // required by Axon
    }

    public record CalendarId(String value) { }
    public record StartDay(String calendarId, int day) { }
    public record FinishDay(String calendarId, int day) { }
    public record DayStarted(String calendarId, int day) { }
    public record DayFinished(String calendarId, int day) { }
}
