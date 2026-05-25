package com.example.orders.commands;

import org.axonframework.commandhandling.RoutingKey;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

/**
 * AF4 command payload. Has @TargetAggregateIdentifier on the aggregate id field
 * and @RoutingKey on a secondary field (warehouseId) — the routing identifier
 * differs from the target aggregate identifier.
 *
 * AF5 migration: add @Command(routingKey = "warehouseId") at the class level,
 * remove @TargetAggregateIdentifier and @RoutingKey field annotations.
 */
public record ShipOrderCommand(
        @TargetAggregateIdentifier String orderId,
        @RoutingKey String warehouseId,
        String address
) {
}
