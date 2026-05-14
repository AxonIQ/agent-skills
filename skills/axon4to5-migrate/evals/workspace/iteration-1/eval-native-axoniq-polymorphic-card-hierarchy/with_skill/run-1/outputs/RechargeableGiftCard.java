package com.example.poly;

import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

public class RechargeableGiftCard extends Card {

    @CommandHandler
    public static void handle(IssueRechargeableCommand cmd, EventAppender appender) {
        appender.append(new RechargeableCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @EventSourcingHandler
    void on(RechargeableCardIssuedEvent e) {
        this.cardId = e.cardId();
        this.balance = e.amount();
    }

    @CommandHandler
    void handle(RechargeCommand cmd, EventAppender appender) {
        appender.append(new CardRechargedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler
    void on(CardRechargedEvent e) {
        this.balance += e.amount();
    }

    @EntityCreator
    public RechargeableGiftCard() {
    }

    public record IssueRechargeableCommand(String cardId, int amount) {}
    public record RechargeCommand(String cardId, int amount) {}
    public record RechargeableCardIssuedEvent(String cardId, int amount) {}
    public record CardRechargedEvent(String cardId, int amount) {}
}
