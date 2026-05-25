# @EntityCreator — No-Arg Constructor Annotation

AF5 requires the no-arg constructor of an aggregate (and of child entities) to be annotated with `@EntityCreator`.
This tells the framework which constructor to use when materializing an empty entity before replaying events.
In AF4 the no-arg constructor was required but had no annotation.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| *(no annotation on no-arg constructor)* | `org.axonframework.eventsourcing.annotation.reflection.EntityCreator` |

## Detection

```bash
# Find aggregate classes and check their no-arg constructors
grep -rn '@EventSourced\|@EventSourcedEntity' --include='*.java' --include='*.kt' --include='*.scala' -l .
```

## Axon Framework 4 Code

```java
@Aggregate
public class Order {

    @AggregateIdentifier
    private OrderId orderId;

    // Required by Axon, no annotation
    protected Order() { }

    // other constructors / handlers...
}
```

## Axon Framework 5 Code

```java
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;

@EventSourced(tagKey = "Order", idType = OrderId.class)
public class Order {

    @EntityCreator
    protected Order() { }

    // other constructors / handlers...
}
```

## Notes

- **Required on child entities too** — every class annotated `@EntityMember`'s no-arg constructor needs
  `@EntityCreator`.
- **`.reflection.` infix is mandatory** — `org.axonframework.eventsourcing.annotation.reflection.EntityCreator`.
  The path without `.reflection.` does not exist.
- **Visibility** — the no-arg constructor may be `protected` or package-private; it does NOT need to be `public`.
- **Omitting `@EntityCreator`** causes a runtime failure when the framework attempts to instantiate the entity —
  the failure message mentions missing creator constructor.
- **OpenRewrite status:** Full — `AddEntityCreatorAnnotation` (in `axon4-to-axon5-eventsourcing.yml`) annotates the no-arg constructor of every `@EventSourced` / `@EventSourcedEntity` class.
