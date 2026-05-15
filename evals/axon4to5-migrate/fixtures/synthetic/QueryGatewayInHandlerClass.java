package com.example.automation;

import com.example.commands.ReserveInventoryCommand;
import com.example.queries.GetInventoryStatus;
import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.queryhandling.QueryGateway;
import org.springframework.stereotype.Component;

@Component
@ProcessingGroup("Automation_Inventory")
class QueryGatewayInHandlerClass {

    private final QueryGateway queryGateway;

    QueryGatewayInHandlerClass(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    @EventHandler
    public void on(OrderPlacedEvent event) {
        var status = queryGateway.query(new GetInventoryStatus(event.itemId()), InventoryStatus.class).join();
        if (status.hasStock()) {
            // dispatch command inline (out of scope — event-processor recipe owns this)
        }
    }
}
