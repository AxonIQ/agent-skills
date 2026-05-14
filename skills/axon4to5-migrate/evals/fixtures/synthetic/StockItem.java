package com.example.inventory;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.EntityId;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

public class StockItem {

    @EntityId
    private String sku;
    private int quantity;

    public StockItem() {
    }

    public StockItem(String sku, int quantity) {
        this.sku = sku;
        this.quantity = quantity;
    }

    @CommandHandler
    void handle(Inventory.AddStockItem cmd) {
        apply(new Inventory.StockItemAdded("", cmd.sku(), cmd.quantity()));
    }

    @EventSourcingHandler
    void on(Inventory.StockItemAdded e) {
        this.quantity += e.quantity();
    }
}
