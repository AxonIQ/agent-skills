---
atom-id: event-appender
title: "AggregateLifecycle.apply(…) → EventAppender.append(…)"
af4-symbols: ["AggregateLifecycle.apply", "AggregateLifecycle", "org.axonframework.modelling.command.AggregateLifecycle"]
af5-symbols: ["EventAppender", "eventAppender.append", "org.axonframework.messaging.eventhandling.gateway.EventAppender"]
detect: grep -rn 'AggregateLifecycle\.apply\|import.*AggregateLifecycle' --include='*.java' --include='*.kt' --include='*.scala' .
used-by: [aggregate]
---

# AggregateLifecycle.apply(…) → EventAppender.append(…)

AF4 used a `ThreadLocal`-backed static method `AggregateLifecycle.apply(event)` to publish events from inside
`@CommandHandler` methods. AF5 removes `ThreadLocal` entirely and replaces this with an `EventAppender` parameter
injected into every `@CommandHandler`.

## Detect

```bash
grep -rn 'AggregateLifecycle\.apply\|import.*AggregateLifecycle' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Before (AF4)

```java
import static org.axonframework.modelling.command.AggregateLifecycle.apply;
// or:
import org.axonframework.modelling.command.AggregateLifecycle;

@CommandHandler
public void handle(ShipOrderCommand cmd) {
    apply(new OrderShippedEvent(orderId, cmd.getAddress()));
    // or: AggregateLifecycle.apply(new OrderShippedEvent(…));
}
```

## After (AF5)

```java
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@CommandHandler
public void handle(ShipOrderCommand cmd, EventAppender eventAppender) {
    eventAppender.append(new OrderShippedEvent(orderId, cmd.getAddress()));
}
```

## Rules

1. **Every `@CommandHandler`** on the aggregate (and on child entities) gets `EventAppender eventAppender` as its
   **last** parameter.
2. Every `AggregateLifecycle.apply(event)` call becomes `eventAppender.append(event)`.
3. Remove the static import `import static org.axonframework.modelling.command.AggregateLifecycle.apply` and the
   regular import `import org.axonframework.modelling.command.AggregateLifecycle`.
4. For **static `@CommandHandler`** methods (ALWAYS creation pattern), `EventAppender` is still a parameter —
   static methods can receive injected parameters just as instance methods do.

## Import

`org.axonframework.messaging.eventhandling.gateway.EventAppender`

⚠️ The **`.messaging.`** infix is mandatory — `org.axonframework.eventhandling.gateway.EventAppender` (no
`.messaging.`) does not exist.

## Multi-event appending

`EventAppender.append(…)` accepts one event at a time. To replicate the AF4 idiom
`apply(event1); apply(event2);` use two separate calls:

```java
eventAppender.append(new Event1(…));
eventAppender.append(new Event2(…));
```

## Gotchas

- **`.messaging.` infix** — LLMs almost always omit this. Verify with grep after editing.
- **Static `@CommandHandler`** — still needs `EventAppender` as a parameter; this is often missed.
- **Child entities** — every `@CommandHandler` on a child entity also needs `EventAppender`. The parent aggregate's
  `EventAppender` is NOT shared; the framework injects a fresh one per method call.
- **No `AggregateLifecycle.apply` should remain** — grep after migration. Any surviving call is a compile error
  (class removed in AF5).

## Used By

- **[[aggregate]]** — common steps (always), threaded into every `@CommandHandler`
- **[[command-handler]]** — command handler methods gain `EventAppender` as last parameter
