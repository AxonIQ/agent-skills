# @TargetAggregateIdentifier Removal

AF4 required a `@TargetAggregateIdentifier` annotation on the command field that routes the command to the
correct aggregate instance. AF5 removes this annotation — routing is now driven by the `idType` declared on
`@EventSourced` and the command's field type.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.modelling.command.TargetAggregateIdentifier` | *(remove — no replacement)* |

## Detection

```bash
grep -rn '@TargetAggregateIdentifier\|TargetAggregateIdentifier' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import org.axonframework.modelling.command.TargetAggregateIdentifier;

public record CreateOrderCommand(
    @TargetAggregateIdentifier OrderId orderId,
    String customerId
) {}
```

## Axon Framework 5 Code

```java
public record CreateOrderCommand(
    OrderId orderId,
    String customerId
) {}
```

## Notes

- **Remove the annotation and its import.** No replacement needed.
- **Remove `@TargetAggregateVersion` too** if present — also gone in AF5.
- AF5 routes commands by matching the command's field type against the aggregate's `idType = OrderId.class`
  declared on `@EventSourced`. The field name is irrelevant; the type match is the routing key.
- If two fields share the same type as `idType`, routing is ambiguous — rename one or use a wrapper type.
