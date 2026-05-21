# @AggregateMember → @EntityMember (Child Entities)

AF4 used `@AggregateMember` to declare child entity collections within an aggregate. AF5 renames this to
`@EntityMember`. Child entities do NOT carry a class-level `@EventSourced`/`@EventSourcedEntity` — they are
discovered through the parent.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.modelling.command.AggregateMember` | `org.axonframework.modelling.entity.annotation.EntityMember` |

## Detection

```bash
grep -rn '@AggregateMember' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import org.axonframework.modelling.command.AggregateMember;

@Aggregate
public class Order {

    @AggregateMember
    private List<OrderLine> lines;

    @AggregateMember(routingKey = "lineId")
    private List<OrderLine> detailedLines;
}
```

## Axon Framework 5 Code

```java
import org.axonframework.modelling.entity.annotation.EntityMember;

@EventSourced(tagKey = "Order", idType = OrderId.class)
public class Order {

    @EntityMember
    private List<OrderLine> lines;

    @EntityMember(routingKey = "lineId")
    private List<OrderLine> detailedLines;
}
```

## Child entity requirements

Each child entity class must:
1. **NOT** carry `@EventSourced`/`@EventSourcedEntity` — discovered through the parent.
2. Have `@EntityCreator` on one constructor.
3. Use `EventAppender eventAppender` in its own `@CommandHandler` methods.

```java
// AF5 child entity
public class OrderLine {

    @EntityCreator
    public OrderLine() {}

    @CommandHandler
    public void handle(UpdateLineCommand cmd, EventAppender eventAppender) {
        eventAppender.append(new LineUpdatedEvent(cmd.lineId(), cmd.quantity()));
    }
}
```

## Notes

- **`Map<K, V>` is a blocker** — `@EntityMember` supports `List<V>` only. Rewrite as `List<V>` with
  internal id management before applying this pattern.
- **`routingKey`** attribute carries over unchanged from `@AggregateMember`.
