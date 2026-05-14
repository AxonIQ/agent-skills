package com.example.giftcard;

import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.extension.spring.stereotype.EventSourced;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;
import org.axonframework.modelling.annotation.TargetEntityId;
import org.axonframework.modelling.entity.annotation.EntityMember;

import java.util.ArrayList;
import java.util.List;

@EventSourced(tagKey = "GiftCard", idType = String.class)
public class GiftCard {

    private String cardId;
    private int balance;

    @EntityMember(routingKey = "txId")
    private List<Transaction> transactions = new ArrayList<>();

    @CommandHandler
    public GiftCard(IssueCardCommand cmd, EventAppender eventAppender) {
        eventAppender.append(new CardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @EventSourcingHandler
    void on(CardIssuedEvent e) {
        this.cardId = e.cardId();
        this.balance = e.amount();
    }

    @CommandHandler
    void handle(StartTransactionCommand cmd, EventAppender eventAppender) {
        if (cmd.amount() > balance) throw new IllegalStateException("insufficient balance");
        eventAppender.append(new TransactionStartedEvent(cardId, cmd.txId(), cmd.amount()));
    }

    @EventSourcingHandler
    void on(TransactionStartedEvent e) {
        this.balance -= e.amount();
        this.transactions.add(new Transaction(e.txId(), e.amount()));
    }

    @EntityCreator
    GiftCard() {
    }

    public record IssueCardCommand(@TargetEntityId String cardId, int amount) {}
    public record StartTransactionCommand(@TargetEntityId String cardId, String txId, int amount) {}
    public record CardIssuedEvent(String cardId, int amount) {}
    public record TransactionStartedEvent(String cardId, String txId, int amount) {}
}
