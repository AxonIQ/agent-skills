package fixtures.state_stored;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.TargetAggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;

/**
 * AF4 STATE-STORED aggregate (JPA-backed, NOT event-sourced).
 *
 * Observable shape:
 *   - @Aggregate stereotype present
 *   - @Entity + @Id (JPA) — state persisted directly
 *   - @AggregateIdentifier on the same field as @Id
 *   - NO @EventSourcingHandler methods anywhere on the class
 *   - Command handlers mutate fields directly instead of applying events
 *
 * The skill MUST detect this pattern and STOP without rewriting. State-stored
 * aggregates are not supported by the AF5 event-sourced entity migration path;
 * they require a separate migration strategy.
 */
@Aggregate
@Entity
public class Customer {

    @Id
    @AggregateIdentifier
    @Column(name = "customer_id")
    private String customerId;

    @Column(name = "name")
    private String name;

    @Column(name = "email")
    private String email;

    @Column(name = "active")
    private boolean active;

    protected Customer() {
    }

    @CommandHandler
    public Customer(RegisterCustomerCommand cmd) {
        this.customerId = cmd.getCustomerId();
        this.name = cmd.getName();
        this.email = cmd.getEmail();
        this.active = true;
    }

    @CommandHandler
    public void handle(UpdateEmailCommand cmd) {
        this.email = cmd.getEmail();
    }

    @CommandHandler
    public void handle(DeactivateCustomerCommand cmd) {
        this.active = false;
    }

    public String getCustomerId() { return customerId; }
    public String getName() { return name; }
    public String getEmail() { return email; }
    public boolean isActive() { return active; }

    // --- Commands ------------------------------------------------------

    public static class RegisterCustomerCommand {
        private final String customerId;
        private final String name;
        private final String email;

        public RegisterCustomerCommand(String customerId, String name, String email) {
            this.customerId = customerId;
            this.name = name;
            this.email = email;
        }

        public String getCustomerId() { return customerId; }
        public String getName() { return name; }
        public String getEmail() { return email; }
    }

    public static class UpdateEmailCommand {
        @TargetAggregateIdentifier
        private final String customerId;
        private final String email;

        public UpdateEmailCommand(String customerId, String email) {
            this.customerId = customerId;
            this.email = email;
        }

        public String getCustomerId() { return customerId; }
        public String getEmail() { return email; }
    }

    public static class DeactivateCustomerCommand {
        @TargetAggregateIdentifier
        private final String customerId;

        public DeactivateCustomerCommand(String customerId) {
            this.customerId = customerId;
        }

        public String getCustomerId() { return customerId; }
    }
}
