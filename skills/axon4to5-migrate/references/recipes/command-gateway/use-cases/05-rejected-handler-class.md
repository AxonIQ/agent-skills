# 05 — Rejected: handler class with `CommandGateway` field

**Why this case is interesting:** A class that injects `CommandGateway` as a field AND has handler annotations (`@EventHandler`, `@CommandHandler`, etc.) looks like a target for this recipe at first glance — it imports `CommandGateway`. But the presence of handler annotations makes it an event-handling component, NOT a top-of-chain caller. The command-gateway recipe must reject it and route to the event-processor recipe (which owns Step 4: `CommandGateway` → `CommandDispatcher` inside a handler).

**Apply-condition:** `$SOURCE` has any method annotated `@EventHandler` / `@CommandHandler` / `@QueryHandler` / `@SagaEventHandler` / `@MessageHandlerInterceptor` (predicate 2 fires).

## Example (AF4 source — NOT touched by this recipe)

```java
package com.example.automation;

import com.example.events.OrderPlacedEvent;
import com.example.commands.ReserveInventoryCommand;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.stereotype.Component;

@Component
@ProcessingGroup("Automation_OrderInventory")
class WhenOrderPlacedReserveInventoryProcessor {

    private final CommandGateway commandGateway;  // <-- has CommandGateway

    WhenOrderPlacedReserveInventoryProcessor(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @EventHandler   // <-- this triggers Applicable predicate 2
    public void on(OrderPlacedEvent event) {
        commandGateway.sendAndWait(new ReserveInventoryCommand(event.orderId()));
    }
}
```

## Expected result

The command-gateway recipe returns Rejected immediately. The source is untouched.

```
return REJECTED

> **Result:** ⏭️ Rejected
> **Source:** `com.example.automation.WhenOrderPlacedReserveInventoryProcessor`
> **Recipe:** axon4to5-command-gateway
>
> **Notes:** Applicable predicate 2 failed — class has `@EventHandler` methods. This is an event-handling component, not a top-of-chain caller. Route to the event-processor recipe; it owns in-handler command dispatch via `CommandDispatcher` (Step 4).
```

## What changed

Nothing — the recipe did not touch the file.

## Caveats

- **The event-processor recipe (Step 4) owns this migration**, not the command-gateway recipe. The correct migration for in-handler dispatch is: remove the `CommandGateway` field + add `CommandDispatcher commandDispatcher` as a method parameter.
- **Do NOT apply command-gateway toolbox steps to the `CommandGateway` import in this class.** If you swap the import to AF5 `CommandGateway` and leave the field, the event-processor recipe will find an inconsistent state and emit a Learning. Leave the class fully untouched.
- **Mixed class (some methods are handlers, some are genuinely top-of-chain)**: in practice, this shape is rare. If encountered, run the handler recipe first; the command-gateway recipe can touch the non-handler methods on follow-up.
