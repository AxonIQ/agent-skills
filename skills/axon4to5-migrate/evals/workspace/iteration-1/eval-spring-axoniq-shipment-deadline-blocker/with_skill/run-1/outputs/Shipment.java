package com.example.shipment;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.deadline.DeadlineManager;
import org.axonframework.deadline.annotation.DeadlineHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;

import java.time.Duration;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
public class Shipment {

    @AggregateIdentifier
    private String shipmentId;
    private String deadlineId;
    private boolean delivered;

    @CommandHandler
    public Shipment(StartShipment command, DeadlineManager deadlineManager) {
        apply(new ShipmentStarted(command.shipmentId()));
        this.deadlineId = deadlineManager.schedule(
                Duration.ofDays(2), "shipment-overdue", command.shipmentId());
    }

    @EventSourcingHandler
    void on(ShipmentStarted event) {
        this.shipmentId = event.shipmentId();
        this.delivered = false;
    }

    @CommandHandler
    void handle(MarkDelivered command, DeadlineManager deadlineManager) {
        if (delivered) throw new IllegalStateException("already delivered");
        apply(new ShipmentDelivered(shipmentId));
        deadlineManager.cancelSchedule("shipment-overdue", deadlineId);
    }

    @EventSourcingHandler
    void on(ShipmentDelivered event) {
        this.delivered = true;
    }

    @DeadlineHandler(deadlineName = "shipment-overdue")
    void onOverdue(String shipmentIdPayload) {
        apply(new ShipmentOverdue(shipmentId));
    }

    @EventSourcingHandler
    void on(ShipmentOverdue event) {
    }

    Shipment() {
    }

    public record StartShipment(String shipmentId) {}
    public record MarkDelivered(String shipmentId) {}
    public record ShipmentStarted(String shipmentId) {}
    public record ShipmentDelivered(String shipmentId) {}
    public record ShipmentOverdue(String shipmentId) {}
}
