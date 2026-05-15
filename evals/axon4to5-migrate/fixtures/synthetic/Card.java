package com.example.poly;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.AggregateRoot;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@AggregateRoot
public abstract class Card {

    @AggregateIdentifier
    protected String cardId;
    protected int balance;

    @CommandHandler
    void handle(DebitCardCommand cmd) {
        if (cmd.amount() > balance) throw new IllegalStateException("insufficient balance");
        apply(new CardDebitedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler
    void on(CardDebitedEvent e) {
        this.balance -= e.amount();
    }

    Card() {
    }

    public record DebitCardCommand(String cardId, int amount) {}
    public record CardDebitedEvent(String cardId, int amount) {}
}
