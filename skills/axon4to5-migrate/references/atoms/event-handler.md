---
atom-id: event-handler
title: "@EventHandler, @DisallowReplay, @ResetHandler — import package moves"
af4-symbols: ["org.axonframework.eventhandling.EventHandler", "org.axonframework.eventhandling.DisallowReplay", "org.axonframework.eventhandling.ResetHandler"]
af5-symbols: ["org.axonframework.messaging.eventhandling.annotation.EventHandler", "org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay", "org.axonframework.messaging.eventhandling.replay.annotation.ResetHandler"]
detect: grep -rn 'import org.axonframework.eventhandling.EventHandler\|import org.axonframework.eventhandling.DisallowReplay\|import org.axonframework.eventhandling.ResetHandler' --include='*.java' --include='*.kt' --include='*.scala' .
used-by: [event-processor, saga]
---

# @EventHandler, @DisallowReplay, @ResetHandler — Import Package Moves

The event-handling annotations moved from the `eventhandling` root package to `messaging.eventhandling.annotation`
(or `…replay.annotation` for replay-related ones). Method signatures are unchanged — only imports change.

## Detect

```bash
grep -rn 'import org\.axonframework\.eventhandling\.\(EventHandler\|DisallowReplay\|ResetHandler\)' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Transforms

### @EventHandler

**Remove:**
```java
import org.axonframework.eventhandling.EventHandler;
```

**Add:**
```java
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
```

### @DisallowReplay

**Remove:**
```java
import org.axonframework.eventhandling.DisallowReplay;
```

**Add:**
```java
import org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay;
```

### @ResetHandler

**Remove:**
```java
import org.axonframework.eventhandling.ResetHandler;
```

**Add:**
```java
import org.axonframework.messaging.eventhandling.replay.annotation.ResetHandler;
```

### @ResetHandler body — no change

`@ResetHandler` migration is **purely an import swap**. The method body and signature remain identical.

## Full example

```java
// AF4
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.eventhandling.DisallowReplay;
import org.axonframework.eventhandling.ResetHandler;

@ProcessingGroup("orders")
public class OrderProjector {

    @EventHandler
    @DisallowReplay
    public void on(OrderCreatedEvent event) { … }

    @ResetHandler
    public void onReset() { … }
}

// AF5
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay;
import org.axonframework.messaging.eventhandling.replay.annotation.ResetHandler;

@Namespace("orders")
public class OrderProjector {

    @EventHandler
    @DisallowReplay
    public void on(OrderCreatedEvent event) { … }

    @ResetHandler
    public void onReset() { … }
}
```

## Gotchas

- **OpenRewrite Phase 1 typically fixes `@EventHandler`** but often leaves `@DisallowReplay` and `@ResetHandler`
  imports in their AF4 locations. Always grep after Phase 1.
- **`@EventHandler` in aggregates** — within an aggregate, event-handling uses `@EventSourcingHandler` (for state
  evolution), NOT `@EventHandler`. If you see `@EventHandler` on an aggregate class, that may be a misconfiguration
  in AF4 — surface as a Learning but do not block.

## Used By

- **[[event-processor]]** — common steps 2 (always; every @EventHandler class in scope)
- **[[saga]]** — not directly, but saga event handlers use a different annotation (`@SagaEventHandler`) which is
  in the legacy package and needs separate treatment
