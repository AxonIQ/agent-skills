package com.example.giftcard;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.AggregateMember;
import org.axonframework.modelling.command.TargetAggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;

import java.util.ArrayList;
import java.util.List;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
public class GiftCard {

    @AggregateIdentifier
    private String cardId;
    private int balance;

    @AggregateMember
    private List<Transaction> transactions = new ArrayList<>();

    @CommandHandler
    public GiftCard(IssueCardCommand cmd) {
        apply(new CardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @EventSourcingHandler
    void on(CardIssuedEvent e) {
        this.cardId = e.cardId();
        this.balance = e.amount();
    }

    @CommandHandler
    void handle(StartTransactionCommand cmd) {
        if (cmd.amount() > balance) throw new IllegalStateException("insufficient balance");
        apply(new TransactionStartedEvent(cardId, cmd.txId(), cmd.amount()));
    }

    @EventSourcingHandler
    void on(TransactionStartedEvent e) {
        this.balance -= e.amount();
        this.transactions.add(new Transaction(e.txId(), e.amount()));
    }

    GiftCard() {
    }

    public record IssueCardCommand(@TargetAggregateIdentifier String cardId, int amount) {}
    public record StartTransactionCommand(@TargetAggregateIdentifier String cardId, String txId, int amount) {}
    public record CardIssuedEvent(String cardId, int amount) {}
    public record TransactionStartedEvent(String cardId, String txId, int amount) {}
}
