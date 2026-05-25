# EventBus → EventSink

AF4 exposed `EventBus` as the SPI for publishing events outside an aggregate (REST controllers, scheduled tasks,
infrastructure bootstrappers). AF5 renames it to `EventSink` — the publish-only role is now in the type name. The
method shape is unchanged: `publish(EventMessage…)` still exists.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.eventhandling.EventBus` | `org.axonframework.messaging.eventhandling.EventSink` |

## Detection

```bash
grep -rn '\bEventBus\b\|import.*eventhandling\.EventBus' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import org.axonframework.eventhandling.EventBus;
import org.axonframework.eventhandling.GenericEventMessage;

@RestController
public class OrderIngestController {

    private final EventBus eventBus;

    public OrderIngestController(EventBus eventBus) {
        this.eventBus = eventBus;
    }

    @PostMapping("/orders/ingest")
    public void ingest(@RequestBody OrderImported event) {
        eventBus.publish(new GenericEventMessage<>(event));
    }
}
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.eventhandling.EventSink;
import org.axonframework.messaging.eventhandling.GenericEventMessage;

@RestController
public class OrderIngestController {

    private final EventSink eventSink;

    public OrderIngestController(EventSink eventSink) {
        this.eventSink = eventSink;
    }

    @PostMapping("/orders/ingest")
    public void ingest(@RequestBody OrderImported event) {
        eventSink.publish(new GenericEventMessage<>(event));
    }
}
```

## Notes

- **Use `EventSink` from REST / CLI / scheduled tasks** — the top-level entry points that have no
  `ProcessingContext`. Inside `@CommandHandler` methods on an aggregate, use the injected `EventAppender`
  (see `aggregate-lifecycle.md`); never inject `EventSink` into an aggregate.
- **Rename only — no body changes required.** `publish(...)` keeps the same overloads. Field name, constructor
  parameter, and any local variables are conventionally renamed `eventBus` → `eventSink` for readability but the
  compiler does not require it.
- AF5 keeps `EventStore` (event-sourced storage) and `EventSink` (publish SPI) as distinct concerns. Code that
  read from the store via `EventBus` was already going through `EventStore` — that path is unaffected by this
  rename.
- **OpenRewrite status:** Full — `ChangeType` rule in `axon4-to-axon5-messaging.yml` rewrites
  `org.axonframework.messaging.eventhandling.EventBus` → `…EventSink` (after the upstream `ChangePackage` moves
  `eventhandling` under `messaging.eventhandling`). The field/variable name change is cosmetic and not performed
  by the recipe.
