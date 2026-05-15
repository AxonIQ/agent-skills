package com.example.bike;

// AF4 aggregate with EventCountSnapshotTriggerDefinition-based snapshot trigger.
// Companion bean: BikeSnapshotDefinition.java extends EventCountSnapshotTriggerDefinition(snapshotter, 10).
// Auto-migration target (native path): @EventSourcedEntity + EventSourcedEntityModule.declarative(...)
//   .snapshotPolicy(c -> SnapshotPolicy.afterEvents(10)).

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate(snapshotTriggerDefinition = "bikeSnapshotDefinition")
public class Bike {

    @AggregateIdentifier
    private String bikeId;
    private boolean available;

    protected Bike() {}

    @CommandHandler
    public Bike(RegisterBike command) {
        apply(new BikeRegistered(command.bikeId()));
    }

    @CommandHandler
    public void handle(RentBike command) {
        if (!available) throw new IllegalStateException("Bike is not available");
        apply(new BikeRented(bikeId, command.renterId()));
    }

    @CommandHandler
    public void handle(ReturnBike command) {
        apply(new BikeReturned(bikeId));
    }

    @EventSourcingHandler
    public void on(BikeRegistered event) {
        this.bikeId = event.bikeId();
        this.available = true;
    }

    @EventSourcingHandler
    public void on(BikeRented event) {
        this.available = false;
    }

    @EventSourcingHandler
    public void on(BikeReturned event) {
        this.available = true;
    }

    public record RegisterBike(String bikeId) {}
    public record RentBike(String renterId) {}
    public record ReturnBike() {}
    public record BikeRegistered(String bikeId) {}
    public record BikeRented(String bikeId, String renterId) {}
    public record BikeReturned(String bikeId) {}
}
