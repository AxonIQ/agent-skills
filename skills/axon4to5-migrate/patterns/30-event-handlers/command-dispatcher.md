# In-Handler Command Dispatch — CommandGateway → CommandDispatcher

AF4 injected `CommandGateway` as a class-level field in event processors that dispatched commands from inside
`@EventHandler` methods. AF5 replaces this with `CommandDispatcher` injected as a **method parameter** — the
framework automatically binds it to the active `ProcessingContext`. The dispatch API is **async** in AF5.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.commandhandling.gateway.CommandGateway` | *(remove field/constructor injection)* |
| — | `org.axonframework.messaging.commandhandling.gateway.CommandDispatcher` |
| — | `java.util.concurrent.CompletableFuture` |

## Detection

```bash
# Find event-handling classes that inject CommandGateway
grep -rln 'CommandGateway' --include='*.java' --include='*.kt' --include='*.scala' . \
  | xargs grep -l '@EventHandler'
```

## Axon Framework 4 Code

```java
@ProcessingGroup("orders")
@Component
public class OrderAutomation {

    private final CommandGateway commandGateway;

    public OrderAutomation(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @EventHandler
    public void on(PaymentReceivedEvent event,
                   @MetaDataValue("gameId") String gameId) {
        commandGateway.sendAndWait(
            new ShipOrderCommand(event.orderId()),
            MetaData.with("gameId", gameId)
        );
    }
}
```

## Axon Framework 5 Code

```java
@Namespace("orders")
@Component
public class OrderAutomation {

    // No CommandGateway field or constructor parameter

    @EventHandler
    public CompletableFuture<?> on(PaymentReceivedEvent event,
                                   @MetadataValue("gameId") String gameId,
                                   CommandDispatcher commandDispatcher) {
        return commandDispatcher
            .send(new ShipOrderCommand(event.orderId()), MetaData.with("gameId", gameId))
            .getResultMessage();
    }
}
```

## Key API differences

| AF4 | AF5 |
|-----|-----|
| `commandGateway.sendAndWait(cmd)` | `commandDispatcher.send(cmd).getResultMessage()` → `CompletableFuture` |
| `commandGateway.send(cmd)` | `commandDispatcher.send(cmd)` |
| `commandGateway.sendAndWait(cmd, MetaData.with(…))` | `commandDispatcher.send(cmd, MetaData.with(…)).getResultMessage()` |
| try/catch synchronous | `.exceptionallyCompose(err -> …)` on the future |
| `void` return from handler | `CompletableFuture<?>` return from handler |

## Use `.resultAs(Type.class)` to avoid wildcards

```java
commandDispatcher.send(cmd).resultAs(Void.class)   // returns CompletableFuture<Void>
```

## Notes

- **Remove the `CommandGateway` field AND constructor parameter entirely** — do not keep both.
- **Event handler must return `CompletableFuture<?>`** when it dispatches commands — the framework propagates the
  future correctly. Do not call `.join()` inside the handler (blocks the thread).
- **`CommandDispatcher` only works inside a `ProcessingContext`** — it cannot be used in REST controllers or
  scheduled tasks. For those, keep `CommandGateway` (see command-gateway recipe).
- **Compensation logic**: AF4 try/catch around `sendAndWait` becomes `.exceptionallyCompose(…)` on the future.
  Forgetting this means compensation silently stops on failure.
- **Simple cases** where you do not need the result: `return commandDispatcher.send(cmd).getResultMessage().thenApply(_ -> null);`
