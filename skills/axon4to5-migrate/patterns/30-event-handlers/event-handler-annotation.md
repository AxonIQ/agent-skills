# @EventHandler, @DisallowReplay, @ResetHandler — Import Package Moves

These three event-handling annotations moved to new packages in AF5. Their semantics are unchanged.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.eventhandling.EventHandler` | `org.axonframework.messaging.eventhandling.annotation.EventHandler` |
| `org.axonframework.eventhandling.DisallowReplay` | `org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay` |
| `org.axonframework.eventhandling.ResetHandler` | `org.axonframework.messaging.eventhandling.replay.annotation.ResetHandler` |

## Detection

```bash
grep -rn 'import org\.axonframework\.eventhandling\.\(EventHandler\|DisallowReplay\|ResetHandler\)' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.eventhandling.DisallowReplay;
import org.axonframework.eventhandling.ResetHandler;

@Component
@ProcessingGroup("orders")
@DisallowReplay
public class OrderProjector {

    @EventHandler
    public void on(OrderCreatedEvent event) {
        // handle
    }

    @ResetHandler
    public void onReset() {
        // clear read model
    }
}
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay;
import org.axonframework.messaging.eventhandling.replay.annotation.ResetHandler;

@Component
@Namespace("orders")
@DisallowReplay
public class OrderProjector {

    @EventHandler
    public void on(OrderCreatedEvent event) {
        // handle
    }

    @ResetHandler
    public void onReset() {
        // clear read model
    }
}
```

## Notes

- **Only import paths change** — annotation names, attributes, and usage patterns are identical.
- **`@DisallowReplay` moves to `replay.annotation`** — the `replay.` infix is new; do not omit it.
- **Event handler return type**: handlers that dispatch commands via `CommandDispatcher` must return
  `CompletableFuture<?>` — see [command-dispatcher.md](command-dispatcher.md).
