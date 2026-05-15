# 05 — Rejected: handler class with `QueryGateway` field

**Why this case is interesting:** A class injects `QueryGateway` as a field AND has handler annotations (`@EventHandler`, `@QueryHandler`, etc.). It looks like a candidate at first glance — it imports `QueryGateway`. But the handler annotations make it a message-handling component, NOT a top-of-chain caller. The query-gateway recipe must reject it and route to the appropriate handler recipe.

**Apply-condition:** `$SOURCE` has any method annotated `@EventHandler` / `@CommandHandler` / `@QueryHandler` / `@SagaEventHandler` / `@MessageHandlerInterceptor` (predicate 2 fires).

## Example (AF4 source — NOT touched by this recipe)

```java
package com.example.automation;

import com.example.queries.GetInventoryStatus;
import com.example.commands.ReserveInventoryCommand;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.axonframework.queryhandling.QueryGateway;
import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.stereotype.Component;

@Component
@ProcessingGroup("Automation_Inventory")
class WhenOrderPlacedCheckInventoryProcessor {

    private final QueryGateway queryGateway;  // <-- has QueryGateway
    private final CommandGateway commandGateway;

    WhenOrderPlacedCheckInventoryProcessor(QueryGateway queryGateway, CommandGateway commandGateway) {
        this.queryGateway = queryGateway;
        this.commandGateway = commandGateway;
    }

    @EventHandler   // <-- this triggers Applicable predicate 2
    public void on(OrderPlacedEvent event) {
        // in-handler query dispatch
        var status = queryGateway.query(new GetInventoryStatus(event.itemId()), InventoryStatus.class).join();
        if (status.hasStock()) {
            commandGateway.sendAndWait(new ReserveInventoryCommand(event.orderId(), event.itemId()));
        }
    }
}
```

## Expected result

The query-gateway recipe returns Rejected immediately. The source is untouched.

```
return REJECTED

> **Result:** ⏭️ Rejected
> **Source:** `com.example.automation.WhenOrderPlacedCheckInventoryProcessor`
> **Recipe:** axon4to5-query-gateway
>
> **Notes:** Applicable predicate 2 failed — class has `@EventHandler` methods. This is an event-handling component, not a top-of-chain caller. Route to the event-processor recipe; it owns in-handler query and command dispatch.
```

## What changed

Nothing — the recipe did not touch the file.

## Caveats

- **The event-processor recipe owns in-handler dispatch** — both `QueryGateway` and `CommandGateway` inside a handler are migrated by the event-processor recipe (Step 4).
- **Do NOT swap the `QueryGateway` import to AF5** in this class from inside this recipe. If you partially migrate the import and leave the class, the event-processor recipe will find inconsistent state. Leave the class fully untouched.
- **Mixed class (some methods are handlers, some are top-of-chain callers)**: run the handler recipe first; the query-gateway recipe can touch non-handler call sites on follow-up only after handler migration is complete.
