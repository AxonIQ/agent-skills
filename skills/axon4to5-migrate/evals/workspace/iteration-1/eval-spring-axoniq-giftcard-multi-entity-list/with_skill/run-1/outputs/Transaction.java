package com.example.giftcard;

import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;
import org.axonframework.modelling.annotation.TargetEntityId;

public class Transaction {

    private String txId;
    private int amount;
    private boolean settled;

    @EntityCreator
    Transaction() {
    }

    public Transaction(String txId, int amount) {
        this.txId = txId;
        this.amount = amount;
    }

    @CommandHandler
    void handle(SettleTransactionCommand cmd, EventAppender eventAppender) {
        if (settled) throw new IllegalStateException("already settled");
        eventAppender.append(new TransactionSettledEvent(cmd.cardId(), cmd.txId()));
    }

    @EventSourcingHandler
    void on(TransactionSettledEvent e) {
        if (e.txId().equals(this.txId)) {
            this.settled = true;
        }
    }

    public record SettleTransactionCommand(@TargetEntityId String cardId, String txId) {}
    public record TransactionSettledEvent(String cardId, String txId) {}
}
