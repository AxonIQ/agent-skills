package com.dddheroes.heroesofddd.calendar.write;

import com.dddheroes.heroesofddd.calendar.events.DayStarted;
import com.dddheroes.heroesofddd.calendar.events.DayFinished;
import com.dddheroes.heroesofddd.calendar.write.startday.StartDay;
import com.dddheroes.heroesofddd.calendar.write.finishday.FinishDay;
import org.axonframework.eventsourcing.configuration.EventSourcingConfigurer;
import org.axonframework.eventsourcing.configuration.EventSourcedEntityModule;
import org.axonframework.test.fixture.AxonTestFixture;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class CalendarTest {

    private AxonTestFixture fixture;

    @BeforeEach
    void setUp() {
        fixture = AxonTestFixture.with(
                EventSourcingConfigurer.create()
                        .registerEntity(EventSourcedEntityModule.autodetected(CalendarId.class, Calendar.class))
        );
    }

    @AfterEach
    void tearDown() {
        fixture.stop();
    }

    @Test
    void startsDayOne() {
        fixture.given().noPriorActivity()
               .when().command(new StartDay("cal-1", 1, 1, 1))
               .then().events(DayStarted.event("cal-1", 1, 1, 1));
    }

    @Test
    void finishesCurrentDay() {
        fixture.given().events(DayStarted.event("cal-1", 1, 1, 1))
               .when().command(new FinishDay("cal-1", 1, 1, 1))
               .then().events(DayFinished.event("cal-1", 1, 1, 1));
    }
}
