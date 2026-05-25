# @TargetAggregateIdentifier Removal

AF4 required a `@TargetAggregateIdentifier` annotation on the command field that routes the command to the
correct aggregate instance. AF5 removes this annotation — routing is now driven by the `idType` declared on
`@EventSourced` and the command's field type.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.modelling.command.TargetAggregateIdentifier` | *(remove — no replacement)* |

## Detection

**Pre-migration (AF4 original):**

```bash
grep -rn '@TargetAggregateIdentifier\|TargetAggregateIdentifier' --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
# OR renames to @TargetEntityId — AF5 routes by idType, so AI removes annotation + import
grep -rn '@TargetEntityId\|TargetEntityId' --include='*.java' --include='*.kt' --include='*.scala' .
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

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
- **OpenRewrite status:** Partial — OR's `ChangeType` (in `axon4-to-axon5-modelling.yml`) renames the annotation to `@TargetEntityId` rather than removing it; AI removes both the annotation and its import since AF5 routes by `idType` instead.
