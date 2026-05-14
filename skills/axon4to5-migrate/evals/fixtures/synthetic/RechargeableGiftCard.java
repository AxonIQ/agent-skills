package com.example.poly;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.spring.stereotype.Aggregate;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
public class RechargeableGiftCard extends Card {

    @CommandHandler
    public RechargeableGiftCard(IssueRechargeableCommand cmd) {
        apply(new RechargeableCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @EventSourcingHandler
    void on(RechargeableCardIssuedEvent e) {
        this.cardId = e.cardId();
        this.balance = e.amount();
    }

    @CommandHandler
    void handle(RechargeCommand cmd) {
        apply(new CardRechargedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler
    void on(CardRechargedEvent e) {
        this.balance += e.amount();
    }

    RechargeableGiftCard() {
    }

    public record IssueRechargeableCommand(String cardId, int amount) {}
    public record RechargeCommand(String cardId, int amount) {}
    public record RechargeableCardIssuedEvent(String cardId, int amount) {}
    public record CardRechargedEvent(String cardId, int amount) {}
}
