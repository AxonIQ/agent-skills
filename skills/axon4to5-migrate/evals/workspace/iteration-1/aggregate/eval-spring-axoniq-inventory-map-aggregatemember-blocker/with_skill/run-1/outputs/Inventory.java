package com.example.inventory;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.AggregateMember;
import org.axonframework.spring.stereotype.Aggregate;

import java.util.HashMap;
import java.util.Map;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
public class Inventory {

    @AggregateIdentifier
    private String inventoryId;

    @AggregateMember
    private Map<String, StockItem> items = new HashMap<>();

    @CommandHandler
    public Inventory(CreateInventory cmd) {
        apply(new InventoryCreated(cmd.inventoryId()));
    }

    @EventSourcingHandler
    void on(InventoryCreated e) {
        this.inventoryId = e.inventoryId();
    }

    @CommandHandler
    void handle(AddStockItem cmd) {
        apply(new StockItemAdded(inventoryId, cmd.sku(), cmd.quantity()));
    }

    @EventSourcingHandler
    void on(StockItemAdded e) {
        items.put(e.sku(), new StockItem(e.sku(), e.quantity()));
    }

    Inventory() {
    }

    public record CreateInventory(String inventoryId) {}
    public record AddStockItem(String inventoryId, String sku, int quantity) {}
    public record InventoryCreated(String inventoryId) {}
    public record StockItemAdded(String inventoryId, String sku, int quantity) {}
}
