package com.dddheroes.heroesofddd.calendar.write;

import com.dddheroes.heroesofddd.calendar.events.DayStarted;
import com.dddheroes.heroesofddd.calendar.events.DayFinished;
import com.dddheroes.heroesofddd.calendar.write.startday.StartDay;
import com.dddheroes.heroesofddd.calendar.write.finishday.FinishDay;
import org.axonframework.test.aggregate.AggregateTestFixture;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class CalendarTest {

    private AggregateTestFixture<Calendar> fixture;

    @BeforeEach
    void setUp() {
        fixture = new AggregateTestFixture<>(Calendar.class);
    }

    @Test
    void startsDayOne() {
        fixture.givenNoPriorActivity()
               .when(new StartDay("cal-1", 1, 1, 1))
               .expectEvents(DayStarted.event("cal-1", 1, 1, 1));
    }

    @Test
    void finishesCurrentDay() {
        fixture.given(DayStarted.event("cal-1", 1, 1, 1))
               .when(new FinishDay("cal-1", 1, 1, 1))
               .expectEvents(DayFinished.event("cal-1", 1, 1, 1));
    }
}
