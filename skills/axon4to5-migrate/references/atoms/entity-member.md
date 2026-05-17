---
atom-id: entity-member
title: "@AggregateMember → @EntityMember (child entity collections)"
af4-symbols: ["@AggregateMember", "org.axonframework.modelling.command.AggregateMember"]
af5-symbols: ["@EntityMember", "org.axonframework.modelling.entity.annotation.EntityMember"]
detect: grep -rn '@AggregateMember' --include='*.java' .
used-by: [aggregate]
---

# @AggregateMember → @EntityMember

AF4 used `@AggregateMember` to declare child entity collections within an aggregate. AF5 renames this to
`@EntityMember`. The child entity class itself gains `@EntityCreator` and uses `EventAppender` in its own
`@CommandHandler` methods — it does NOT carry a class-level `@EventSourced`/`@EventSourcedEntity`.

## Detect

```bash
grep -rn '@AggregateMember' --include='*.java' .
```

## Import change

**Remove:**
```java
import org.axonframework.modelling.command.AggregateMember;
```

**Add:**
```java
import org.axonframework.modelling.entity.annotation.EntityMember;
```

## Annotation change

Replace `@AggregateMember` → `@EntityMember` on every annotated field. For collection-typed fields, keep
`routingKey`:

```java
// AF4
@AggregateMember
private List<OrderLine> lines;

@AggregateMember(routingKey = "lineId")
private List<OrderLine> lines;

// AF5
@EntityMember
private List<OrderLine> lines;

@EntityMember(routingKey = "lineId")
private List<OrderLine> lines;
```

## Map-typed `@AggregateMember` → Blocker B2

`@AggregateMember Map<K, V>` has **no AF5 equivalent**. `@EntityMember` supports `List<V>` only. Detect with:

```bash
grep -nE '@AggregateMember[\s\S]{0,200}Map<' <aggregate file>
```

If found: emit Blocker B2 immediately. Do NOT attempt to migrate Map-typed members — the
redesign (Map → List + custom id management) requires changes outside this recipe's scope.

## Child entity requirements

Each child entity class in the aggregate's scope must:

1. **NOT carry** a class-level `@EventSourced`/`@EventSourcedEntity` — it is discovered through the parent.
2. Have `@EntityCreator` on its no-arg constructor (see [[entity-creator]]).
3. Have `EventAppender eventAppender` as the last parameter on each of its own `@CommandHandler` methods
   (see [[event-appender]]).

## Example — full child entity after migration

```java
// Child entity (OrderLine) — AF5 shape
public class OrderLine {

    private String lineId;
    private int quantity;

    @EntityCreator
    public OrderLine() {}

    @CommandHandler
    public void handle(UpdateQuantityCommand cmd, EventAppender eventAppender) {
        eventAppender.append(new QuantityUpdatedEvent(lineId, cmd.getQuantity()));
    }

    @EventSourcingHandler
    protected void on(QuantityUpdatedEvent event) {
        this.quantity = event.getQuantity();
    }
}
```

## Gotchas

- **No class-level stereotype on child entities** — `@EventSourced`/`@EventSourcedEntity` on a child causes
  duplicate registration. Only the root aggregate carries the stereotype.
- **`routingKey` maps to the child's identifier property name** — same as AF4. Keep it during migration.
- **Map → Blocker B2** — never silently convert Map to List; the parent's event-handler bodies and projections
  all need consistent updates that are outside this recipe's scope.

## Used By

- **[[aggregate]]** — Step M (multi-entity), when `@AggregateMember` is detected
