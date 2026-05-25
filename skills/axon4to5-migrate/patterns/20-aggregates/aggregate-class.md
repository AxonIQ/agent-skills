# Aggregate Class Stereotype

AF4 marked event-sourced aggregates with `@Aggregate` (Spring) or `@AggregateRoot` (native configurer) and a
`@AggregateIdentifier` field. AF5 replaces these with `@EventSourced`/`@EventSourcedEntity` on the class — the
identity type is declared as an attribute, not via a field annotation.

## Import Mappings

| AF4 | AF5 (Spring) | AF5 (native) |
|-----|-------------|--------------|
| `org.axonframework.spring.stereotype.Aggregate` | `org.axonframework.extension.spring.stereotype.EventSourced` | — |
| `org.axonframework.modelling.command.AggregateRoot` | — | `org.axonframework.eventsourcing.annotation.EventSourcedEntity` |
| `org.axonframework.modelling.command.AggregateIdentifier` | *(remove — no replacement)* | *(remove)* |

## Detection

```bash
grep -rn '@Aggregate\|@AggregateRoot\|@AggregateIdentifier' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import org.axonframework.spring.stereotype.Aggregate;
import org.axonframework.modelling.command.AggregateIdentifier;

@Aggregate
public class Order {

    @AggregateIdentifier
    private OrderId orderId;

    protected Order() { }  // no annotation
}
```

## Axon Framework 5 Code — Spring Boot (`configuration=spring`)

```java
import org.axonframework.extension.spring.stereotype.EventSourced;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;

@EventSourced(tagKey = "Order", idType = OrderId.class)
public class Order {

    // No @AggregateIdentifier field annotation

    @EntityCreator
    protected Order() { }
}
```

## Axon Framework 5 Code — Native Configurer (`configuration=native`)

```java
import org.axonframework.eventsourcing.annotation.EventSourcedEntity;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;

@EventSourcedEntity(tagKey = "Order", idType = OrderId.class)
public class Order {

    @EntityCreator
    protected Order() { }
}
```

## Required attributes (never omit)

| Attribute | Value | Why |
|-----------|-------|-----|
| `tagKey` | Simple class name string, e.g. `"Order"` | Event routing key — defaults to class name but silently breaks on rename |
| `idType` | Class of the AF4 `@AggregateIdentifier` field, e.g. `OrderId.class` | Default is `String.class`; wrong type → silent identity resolution failure |

## Partial migration state (post-OpenRewrite)

OR rewrites `@Aggregate` → `@EventSourced` and inserts a placeholder `idType = Object.class`. `tagKey` defaults to the simple class name but may still be missing on hand-written / unusual cases. Common half-state:

```java
@EventSourced(tagKey = "Order", idType = Object.class)   // idType is a placeholder
public class Order {
    private OrderId orderId;  // @AggregateIdentifier already stripped
    protected Order() { }     // @EntityCreator NOT added — see entity-creator.md
}
```

Minimal fix: replace `idType = Object.class` with the real id class (`OrderId.class`), confirm `tagKey` matches the simple class name used by event `@EventTag(key = …)`, and add `@EntityCreator` to the no-arg constructor. Do NOT re-add `@AggregateIdentifier` or revert `@EventSourced` to `@Aggregate`. Audit:

```bash
grep -rn 'idType = Object\.class\|@EventSourced[^(]' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Notes

- **`.extension.spring.` infix is mandatory** in Path A — `org.axonframework.extension.spring.stereotype.EventSourced`.
  The path `org.axonframework.spring.stereotype.EventSourced` does not exist; it causes a compile error.
- **Remove `@AggregateIdentifier`** from the field — the identity is now declared on the class annotation.
- **`@EntityCreator` on the no-arg constructor is required** — see [entity-creator.md](entity-creator.md).
- **Snapshot trigger**: if `@Aggregate` carried `snapshotTriggerDefinition`, there is no AF5 equivalent — this is
  a blocker that requires manual resolution.
- **OpenRewrite Phase 1** sometimes rewrites `@Aggregate` → `@EventSourced` without adding `tagKey`/`idType`.
  Always grep for `@EventSourced` without attributes after Phase 1 and add them.
