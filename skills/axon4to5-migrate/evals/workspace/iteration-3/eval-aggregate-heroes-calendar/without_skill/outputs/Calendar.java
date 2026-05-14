package com.dddheroes.heroesofddd.calendar.write;

import com.dddheroes.heroesofddd.calendar.write.finishday.CanOnlyFinishCurrentDay;
import com.dddheroes.heroesofddd.calendar.events.DayFinished;
import com.dddheroes.heroesofddd.calendar.write.finishday.FinishDay;
import com.dddheroes.heroesofddd.calendar.write.startday.CannotSkipDays;
import com.dddheroes.heroesofddd.calendar.events.DayStarted;
import com.dddheroes.heroesofddd.calendar.write.startday.StartDay;
import org.axonframework.commandhandling.annotation.CommandHandler;
import org.axonframework.eventsourcing.annotation.EventSourcedEntity;
import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventhandling.gateway.EventAppender;
import org.axonframework.modelling.annotation.EntityCreator;

@EventSourcedEntity
class Calendar {

    private CalendarId calendarId;
    private Month currentMonth;
    private Week currentWeek;
    private Day currentDay;

    @CommandHandler
    void decide(StartDay command, EventAppender eventAppender) {
        new CannotSkipDays(command, currentMonth, currentWeek, currentDay).verify();

        eventAppender.append(
                DayStarted.event(
                        command.calendarId(),
                        command.month(),
                        command.week(),
                        command.day()
                )
        );
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

        eventAppender.append(
                DayFinished.event(
                        command.calendarId(),
                        command.month(),
                        command.week(),
                        command.day()
                )
        );
    }

    @EntityCreator
    Calendar() {
        // required by Axon
    }
}
