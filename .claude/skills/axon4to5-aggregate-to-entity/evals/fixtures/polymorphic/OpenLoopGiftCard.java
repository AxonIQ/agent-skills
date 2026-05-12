package fixtures.polymorphic;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

public class OpenLoopGiftCard extends GiftCard {

    private String network;

    public OpenLoopGiftCard() {
    }

    @CommandHandler
    public OpenLoopGiftCard(IssueOpenLoopCommand cmd) {
        apply(new OpenLoopIssuedEvent(cmd.getCardId(), cmd.getAmount(), cmd.getNetwork()));
    }

    @EventSourcingHandler
    public void on(OpenLoopIssuedEvent event) {
        this.cardId = event.getCardId();
        this.balance = event.getAmount();
        this.network = event.getNetwork();
    }

    public String getNetwork() {
        return network;
    }

    public static class IssueOpenLoopCommand {
        private final String cardId;
        private final int amount;
        private final String network;

        public IssueOpenLoopCommand(String cardId, int amount, String network) {
            this.cardId = cardId;
            this.amount = amount;
            this.network = network;
        }

        public String getCardId() { return cardId; }
        public int getAmount() { return amount; }
        public String getNetwork() { return network; }
    }

    public static class OpenLoopIssuedEvent {
        private final String cardId;
        private final int amount;
        private final String network;

        public OpenLoopIssuedEvent(String cardId, int amount, String network) {
            this.cardId = cardId;
            this.amount = amount;
            this.network = network;
        }

        public String getCardId() { return cardId; }
        public int getAmount() { return amount; }
        public String getNetwork() { return network; }
    }
}
