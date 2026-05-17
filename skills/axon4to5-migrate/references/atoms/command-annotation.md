---
atom-id: command-annotation
title: "Command classes — @Command annotation + @TargetAggregateIdentifier → @TargetEntityId"
af4-symbols: ["@TargetAggregateIdentifier", "org.axonframework.modelling.command.TargetAggregateIdentifier", "@RoutingKey"]
af5-symbols: ["@Command", "@TargetEntityId", "org.axonframework.messaging.commandhandling.annotation.Command", "org.axonframework.modelling.annotation.TargetEntityId"]
detect: grep -rn 'TargetAggregateIdentifier\|@RoutingKey' --include='*.java' --include='*.kt' --include='*.scala' .
used-by: [aggregate]
---

# Command Classes — @Command + @TargetEntityId

AF4 command classes used `@TargetAggregateIdentifier` to route commands to the correct aggregate instance. AF5
replaces this with `@TargetEntityId` and requires command classes to carry the `@Command` class-level annotation.

## Detect

```bash
grep -rn 'TargetAggregateIdentifier\|@RoutingKey' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Transforms

### 1. Add `@Command` to the class

Every command class that is handled by a `@CommandHandler` on an aggregate must be annotated `@Command`.

```java
// AF4
public class ShipOrderCommand {
    @TargetAggregateIdentifier
    private final OrderId orderId;
    // ...
}

// AF5
import org.axonframework.messaging.commandhandling.annotation.Command;
import org.axonframework.modelling.annotation.TargetEntityId;

@Command
public class ShipOrderCommand {
    @TargetEntityId
    private final OrderId orderId;
    // ...
}
```

### 2. `@TargetAggregateIdentifier` → `@TargetEntityId`

**Remove:**
```java
import org.axonframework.modelling.command.TargetAggregateIdentifier;
@TargetAggregateIdentifier
```

**Add:**
```java
import org.axonframework.modelling.annotation.TargetEntityId;
@TargetEntityId
```

### 3. `@RoutingKey` → `@Command(routingKey = "…")`

When a command class used `@RoutingKey` on a field:

**Remove:**
```java
@RoutingKey
private final OrderId orderId;
```

**Replace with** (routing key moved to class annotation):
```java
@Command(routingKey = "orderId")
public class ShipOrderCommand {
    private final OrderId orderId;
    // ...
}
```

Remove the `@RoutingKey` annotation and its import.

## Imports

| AF5 annotation | Import |
|---|---|
| `@Command` | `org.axonframework.messaging.commandhandling.annotation.Command` |
| `@TargetEntityId` | `org.axonframework.modelling.annotation.TargetEntityId` |

## Which commands to migrate

Migrate every command class referenced by `@CommandHandler` **first-parameter types** on the aggregate in scope.
Commands used only by event processors, REST controllers, or sagas that do NOT live in the aggregate's scope are
migrated by their respective component recipes — do not migrate them here if they are out of scope.

## Gotchas

- **`@Command` is a class annotation** — it goes on the command class itself, not on the handler method.
- **`routingKey` in `@Command` is the field name as a string** — must match the property name exactly.
- **`@TargetEntityId` replaces `@TargetAggregateIdentifier` 1:1** — same field, just renamed.
- **Command records** — if the command is a Java record, add `@Command` to the record declaration. `@TargetEntityId`
  goes on the record component (`@TargetEntityId OrderId orderId`).

## Used By

- **[[aggregate]]** — common steps, Step: "Commands" (for each command class in scope)
