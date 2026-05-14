package com.example.poly;

import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

public class OpenLoopGiftCard extends Card {

    private boolean activated;

    @CommandHandler
    public static void handle(IssueOpenLoopCommand cmd, EventAppender appender) {
        appender.append(new OpenLoopCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @EventSourcingHandler
    void on(OpenLoopCardIssuedEvent e) {
        this.cardId = e.cardId();
        this.balance = e.amount();
        this.activated = true;
    }

    @EntityCreator
    public OpenLoopGiftCard() {
    }

    public record IssueOpenLoopCommand(String cardId, int amount) {}
    public record OpenLoopCardIssuedEvent(String cardId, int amount) {}
}
