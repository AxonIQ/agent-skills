package com.example.poly;

import org.axonframework.eventsourcing.annotation.EventSourcedEntity;
import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@EventSourcedEntity(
        tagKey = "Card",
        idType = String.class,
        concreteTypes = { OpenLoopGiftCard.class, RechargeableGiftCard.class }
)
public abstract class Card {

    protected String cardId;
    protected int balance;

    @CommandHandler
    void handle(DebitCardCommand cmd, EventAppender appender) {
        if (cmd.amount() > balance) throw new IllegalStateException("insufficient balance");
        appender.append(new CardDebitedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler
    void on(CardDebitedEvent e) {
        this.balance -= e.amount();
    }

    @EntityCreator
    protected Card() {
    }

    public record DebitCardCommand(String cardId, int amount) {}
    public record CardDebitedEvent(String cardId, int amount) {}
}
