package fixtures.polymorphic;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

public abstract class GiftCard extends Card {

    protected GiftCard() {
    }

    @CommandHandler
    public void handle(RedeemCommand cmd) {
        if (cmd.getAmount() > balance) {
            throw new IllegalStateException("Insufficient balance");
        }
        apply(new RedeemedEvent(cardId, cmd.getAmount()));
    }

    @EventSourcingHandler
    public void on(RedeemedEvent event) {
        this.balance -= event.getAmount();
    }

    public static class RedeemCommand {
        @TargetAggregateIdentifier
        private final String cardId;
        private final int amount;

        public RedeemCommand(String cardId, int amount) {
            this.cardId = cardId;
            this.amount = amount;
        }

        public String getCardId() { return cardId; }
        public int getAmount() { return amount; }
    }

    public static class RedeemedEvent {
        private final String cardId;
        private final int amount;

        public RedeemedEvent(String cardId, int amount) {
            this.cardId = cardId;
            this.amount = amount;
        }

        public String getCardId() { return cardId; }
        public int getAmount() { return amount; }
    }
}
