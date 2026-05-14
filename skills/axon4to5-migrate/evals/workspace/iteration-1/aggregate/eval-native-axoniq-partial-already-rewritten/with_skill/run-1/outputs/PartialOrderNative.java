package com.example.order.write;

// Realistic post-OpenRewrite-Phase-1 partial state for configuration=native (framework Configurer):
// - @AggregateRoot was mechanically swapped to @EventSourcedEntity
// - …but tagKey / idType attributes were NOT added (defaults relied on)
// - @AggregateIdentifier still present + import
// - @CommandHandler / @EventSourcingHandler imports STILL AF4 packages
// - AggregateLifecycle.apply(...) STILL in handler bodies
// - No @EntityCreator on the constructor
// - The Configurer wiring file is OUT OF SCOPE for this eval — only the entity source is fed in

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.EventSourcedEntity;
import org.axonframework.modelling.command.AggregateCreationPolicy;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.CreationPolicy;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@EventSourcedEntity
public class PartialOrderNative {

    @AggregateIdentifier
    private String orderId;
    private int itemCount;
    private boolean shipped;

    @CommandHandler
    @CreationPolicy(AggregateCreationPolicy.ALWAYS)
    public void handle(PlaceOrder cmd) {
        apply(new OrderPlaced(cmd.orderId(), cmd.itemCount()));
    }

    @EventSourcingHandler
    void on(OrderPlaced e) {
        this.orderId = e.orderId();
        this.itemCount = e.itemCount();
        this.shipped = false;
    }

    @CommandHandler
    public void handle(ShipOrder cmd) {
        if (shipped) throw new IllegalStateException("already shipped");
        apply(new OrderShipped(cmd.orderId()));
    }

    @EventSourcingHandler
    void on(OrderShipped e) {
        this.shipped = true;
    }

    PartialOrderNative() {
        // required by Axon — no @EntityCreator yet
    }

    public record PlaceOrder(String orderId, int itemCount) { }
    public record ShipOrder(String orderId) { }
    public record OrderPlaced(String orderId, int itemCount) { }
    public record OrderShipped(String orderId) { }
}
