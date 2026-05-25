# Command Class Annotation

AF5 requires every command payload type (record or class) that targets a `@CommandHandler` to carry the `@Command`
annotation. AF4 had no class-level annotation on command payloads — the framework discovered them implicitly via
handler signatures. AF5 makes the contract explicit and folds the AF4 `@RoutingKey` field into a `routingKey`
attribute on `@Command`.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| *(no class annotation)* | `org.axonframework.messaging.commandhandling.annotation.Command` |
| `org.axonframework.commandhandling.RoutingKey` (field annotation) | `@Command(routingKey = "fieldName")` (attribute on `@Command`) |

## Detection

```bash
# Command payloads referenced from @CommandHandler methods; @RoutingKey usages.
grep -rn '@RoutingKey\|@CommandHandler' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
// No class-level annotation. Optional @RoutingKey on a non-target field
// when the routing identifier differs from @TargetAggregateIdentifier.
public record ShipOrderCommand(
    @TargetAggregateIdentifier String orderId,
    @RoutingKey String warehouseId,
    String address
) { }
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.commandhandling.annotation.Command;

@Command(routingKey = "warehouseId")
public record ShipOrderCommand(
    String orderId,
    String warehouseId,
    String address
) { }
```

When the command had no `@RoutingKey`, just add `@Command`:

```java
@Command
public record ShipOrderCommand(String orderId, String address) { }
```

## Notes

- **`@Command` is mandatory** — without it, AF5 cannot dispatch the payload through `CommandDispatcher` /
  `CommandGateway`. The compiler will not catch this; the failure surfaces at runtime as "no handler for command".
- **`routingKey` references the field by name (string)**. Multi-handler scenarios use this to map a single command
  to several entities — the value of that field selects the receiving instance.
- **`@TargetAggregateIdentifier` is removed entirely** (see `target-aggregate-identifier.md`) — the target id is
  resolved by matching the command class to a `@Command`-annotated payload whose `idType` aligns with the entity's
  `@EventSourced(idType = …)`. Do not re-add it as a `routingKey`.
- Plain commands (no special routing) require only `@Command` with no attributes.
- **OpenRewrite status:** Full — `AddCommandAnnotation` (in `axon4-to-axon5-eventsourcing.yml`) scans
  `@CommandHandler` methods, adds `@Command` to their payload types, and migrates `@RoutingKey` field annotations
  into the `routingKey` attribute on `@Command`.
