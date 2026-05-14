package com.example.giftcard;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.EntityId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

public class Transaction {

    @EntityId
    private String txId;
    private int amount;
    private boolean settled;

    Transaction() {
    }

    public Transaction(String txId, int amount) {
        this.txId = txId;
        this.amount = amount;
    }

    @CommandHandler
    void handle(SettleTransactionCommand cmd) {
        if (settled) throw new IllegalStateException("already settled");
        apply(new TransactionSettledEvent(cmd.cardId(), cmd.txId()));
    }

    @EventSourcingHandler
    void on(TransactionSettledEvent e) {
        if (e.txId().equals(this.txId)) {
            this.settled = true;
        }
    }

    public record SettleTransactionCommand(@TargetAggregateIdentifier String cardId, String txId) {}
    public record TransactionSettledEvent(String cardId, String txId) {}
}
