package com.example.order.write;

// Migrated to AF5 Path B (configuration=native):
// - @EventSourcedEntity carries explicit tagKey + idType
// - @AggregateIdentifier removed; orderId is a plain field
// - @CreationPolicy(ALWAYS) → static @CommandHandler factory
// - AF4 @CommandHandler / @EventSourcingHandler imports swapped to AF5 packages
// - AggregateLifecycle.apply(...) → EventAppender.append(...)
// - @EntityCreator on the no-arg constructor

import org.axonframework.eventsourcing.annotation.EventSourcedEntity;
import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@EventSourcedEntity(tagKey = "PartialOrderNative", idType = String.class)
public class PartialOrderNative {

    private String orderId;
    private int itemCount;
    private boolean shipped;

    @CommandHandler
    public static void handle(PlaceOrder cmd, EventAppender appender) {
        appender.append(new OrderPlaced(cmd.orderId(), cmd.itemCount()));
    }

    @EventSourcingHandler
    void on(OrderPlaced e) {
        this.orderId = e.orderId();
        this.itemCount = e.itemCount();
        this.shipped = false;
    }

    @CommandHandler
    public void handle(ShipOrder cmd, EventAppender appender) {
        if (shipped) throw new IllegalStateException("already shipped");
        appender.append(new OrderShipped(cmd.orderId()));
    }

    @EventSourcingHandler
    void on(OrderShipped e) {
        this.shipped = true;
    }

    @EntityCreator
    PartialOrderNative() {
        // required by Axon
    }

    public record PlaceOrder(String orderId, int itemCount) { }
    public record ShipOrder(String orderId) { }
    public record OrderPlaced(String orderId, int itemCount) { }
    public record OrderShipped(String orderId) { }
}
