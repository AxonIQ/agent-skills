package fixtures.multi_entity;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.AggregateMember;
import org.axonframework.modelling.command.EntityId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;

import java.util.ArrayList;
import java.util.List;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
public class GiftCard {

    @AggregateIdentifier
    private String cardId;

    private int remainingValue;

    @AggregateMember
    private List<Transaction> transactions = new ArrayList<>();

    public GiftCard() {
    }

    @CommandHandler
    public GiftCard(IssueCardCommand cmd) {
        apply(new CardIssuedEvent(cmd.getCardId(), cmd.getAmount()));
    }

    @CommandHandler
    public void handle(RedeemCardCommand cmd) {
        if (cmd.getAmount() > remainingValue) {
            throw new IllegalStateException("Insufficient funds");
        }
        apply(new CardRedeemedEvent(cardId, cmd.getAmount(), cmd.getTransactionId()));
    }

    @EventSourcingHandler
    public void on(CardIssuedEvent event) {
        this.cardId = event.getCardId();
        this.remainingValue = event.getAmount();
    }

    @EventSourcingHandler
    public void on(CardRedeemedEvent event) {
        this.remainingValue -= event.getAmount();
        this.transactions.add(new Transaction(event.getTransactionId(), event.getAmount()));
    }

    // --- Child entity --------------------------------------------------

    static class Transaction {

        @EntityId
        private String transactionId;
        private int amount;

        @SuppressWarnings("unused")
        public Transaction() {
        }

        public Transaction(String transactionId, int amount) {
            this.transactionId = transactionId;
            this.amount = amount;
        }

        @CommandHandler
        public void handle(VoidTransactionCommand cmd) {
            apply(new TransactionVoidedEvent(transactionId));
        }

        @EventSourcingHandler
        public void on(TransactionVoidedEvent event) {
            this.amount = 0;
        }
    }

    // --- Commands ------------------------------------------------------

    static class IssueCardCommand {
        private final String cardId;
        private final int amount;

        public IssueCardCommand(String cardId, int amount) {
            this.cardId = cardId;
            this.amount = amount;
        }

        public String getCardId() { return cardId; }
        public int getAmount() { return amount; }
    }

    static class RedeemCardCommand {
        @TargetAggregateIdentifier
        private final String cardId;
        private final String transactionId;
        private final int amount;

        public RedeemCardCommand(String cardId, String transactionId, int amount) {
            this.cardId = cardId;
            this.transactionId = transactionId;
            this.amount = amount;
        }

        public String getCardId() { return cardId; }
        public String getTransactionId() { return transactionId; }
        public int getAmount() { return amount; }
    }

    static class VoidTransactionCommand {
        @TargetAggregateIdentifier
        private final String cardId;
        private final String transactionId;

        public VoidTransactionCommand(String cardId, String transactionId) {
            this.cardId = cardId;
            this.transactionId = transactionId;
        }

        public String getCardId() { return cardId; }
        public String getTransactionId() { return transactionId; }
    }

    // --- Events --------------------------------------------------------

    static class CardIssuedEvent {
        private final String cardId;
        private final int amount;

        public CardIssuedEvent(String cardId, int amount) {
            this.cardId = cardId;
            this.amount = amount;
        }

        public String getCardId() { return cardId; }
        public int getAmount() { return amount; }
    }

    static class CardRedeemedEvent {
        private final String cardId;
        private final int amount;
        private final String transactionId;

        public CardRedeemedEvent(String cardId, int amount, String transactionId) {
            this.cardId = cardId;
            this.amount = amount;
            this.transactionId = transactionId;
        }

        public String getCardId() { return cardId; }
        public int getAmount() { return amount; }
        public String getTransactionId() { return transactionId; }
    }

    static class TransactionVoidedEvent {
        private final String transactionId;

        public TransactionVoidedEvent(String transactionId) {
            this.transactionId = transactionId;
        }

        public String getTransactionId() { return transactionId; }
    }
}
