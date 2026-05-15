package com.example.poly;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.spring.stereotype.Aggregate;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
public class OpenLoopGiftCard extends Card {

    private boolean activated;

    @CommandHandler
    public OpenLoopGiftCard(IssueOpenLoopCommand cmd) {
        apply(new OpenLoopCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @EventSourcingHandler
    void on(OpenLoopCardIssuedEvent e) {
        this.cardId = e.cardId();
        this.balance = e.amount();
        this.activated = true;
    }

    OpenLoopGiftCard() {
    }

    public record IssueOpenLoopCommand(String cardId, int amount) {}
    public record OpenLoopCardIssuedEvent(String cardId, int amount) {}
}
