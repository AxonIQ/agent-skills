package fixtures.polymorphic;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

public class RechargeableGiftCard extends GiftCard {

    public RechargeableGiftCard() {
    }

    @CommandHandler
    public RechargeableGiftCard(IssueRechargeableCommand cmd) {
        apply(new RechargeableIssuedEvent(cmd.getCardId(), cmd.getAmount()));
    }

    @CommandHandler
    public void handle(RechargeCommand cmd) {
        apply(new RechargedEvent(cardId, cmd.getAmount()));
    }

    @EventSourcingHandler
    public void on(RechargeableIssuedEvent event) {
        this.cardId = event.getCardId();
        this.balance = event.getAmount();
    }

    @EventSourcingHandler
    public void on(RechargedEvent event) {
        this.balance += event.getAmount();
    }

    public static class IssueRechargeableCommand {
        private final String cardId;
        private final int amount;

        public IssueRechargeableCommand(String cardId, int amount) {
            this.cardId = cardId;
            this.amount = amount;
        }

        public String getCardId() { return cardId; }
        public int getAmount() { return amount; }
    }

    public static class RechargeCommand {
        @TargetAggregateIdentifier
        private final String cardId;
        private final int amount;

        public RechargeCommand(String cardId, int amount) {
            this.cardId = cardId;
            this.amount = amount;
        }

        public String getCardId() { return cardId; }
        public int getAmount() { return amount; }
    }

    public static class RechargeableIssuedEvent {
        private final String cardId;
        private final int amount;

        public RechargeableIssuedEvent(String cardId, int amount) {
            this.cardId = cardId;
            this.amount = amount;
        }

        public String getCardId() { return cardId; }
        public int getAmount() { return amount; }
    }

    public static class RechargedEvent {
        private final String cardId;
        private final int amount;

        public RechargedEvent(String cardId, int amount) {
            this.cardId = cardId;
            this.amount = amount;
        }

        public String getCardId() { return cardId; }
        public int getAmount() { return amount; }
    }
}
