# 01 — Simple aggregate (Spring)

**Why this case is interesting:** The vanilla "one root, no children,
no creation policy" migration. Establishes the baseline pattern every other
example references — `@Aggregate` → `@EventSourced`, constructor command
handler → `static @CommandHandler` + `@EntityCreator`, `apply(...)` →
`eventAppender.append(...)`, and `@EventTag` on every event id field.

**Variant:** simple, Spring

## Before (AF4)

```java
package com.example.giftcard;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.TargetAggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
public class GiftCard {

    @AggregateIdentifier
    private String cardId;
    private int remainingValue;

    @CommandHandler
    public GiftCard(IssueCardCommand cmd) {
        if (cmd.amount() <= 0) throw new IllegalArgumentException("amount <= 0");
        apply(new CardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @CommandHandler
    public void handle(RedeemCardCommand cmd) {
        if (cmd.amount() > remainingValue) throw new IllegalStateException("insufficient");
        apply(new CardRedeemedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler
    public void on(CardIssuedEvent evt) {
        this.cardId = evt.cardId();
        this.remainingValue = evt.amount();
    }

    @EventSourcingHandler
    public void on(CardRedeemedEvent evt) {
        this.remainingValue -= evt.amount();
    }

    protected GiftCard() { /* required by AF4 */ }
}

// Commands
public record IssueCardCommand(String cardId, int amount) { }
public record RedeemCardCommand(@TargetAggregateIdentifier String cardId, int amount) { }

// Events
public record CardIssuedEvent(String cardId, int amount) { }
public record CardRedeemedEvent(String cardId, int amount) { }
```

## After (AF5)

```java
package com.example.giftcard;

import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.EventTag;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.extension.spring.stereotype.EventSourced;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;
import org.axonframework.modelling.annotation.TargetEntityId;

@EventSourced(tagKey = "GiftCard")
public class GiftCard {

    private String cardId;
    private int remainingValue;

    @EntityCreator
    public GiftCard() { }

    @CommandHandler
    public static void handle(IssueCardCommand cmd, EventAppender eventAppender) {
        if (cmd.amount() <= 0) throw new IllegalArgumentException("amount <= 0");
        eventAppender.append(new CardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @CommandHandler
    public void handle(RedeemCardCommand cmd, EventAppender eventAppender) {
        if (cmd.amount() > remainingValue) throw new IllegalStateException("insufficient");
        eventAppender.append(new CardRedeemedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler
    public void on(CardIssuedEvent evt) {
        this.cardId = evt.cardId();
        this.remainingValue = evt.amount();
    }

    @EventSourcingHandler
    public void on(CardRedeemedEvent evt) {
        this.remainingValue -= evt.amount();
    }
}

// Commands
public record IssueCardCommand(String cardId, int amount) { }
public record RedeemCardCommand(@TargetEntityId String cardId, int amount) { }

// Events — @EventTag wires the event's id field to the entity's tagKey
public record CardIssuedEvent(@EventTag(key = "GiftCard") String cardId, int amount) { }
public record CardRedeemedEvent(@EventTag(key = "GiftCard") String cardId, int amount) { }
```

## What changed

- `@Aggregate` (Spring) → `@EventSourced(tagKey = "GiftCard")` — `idType` omitted because the id is `String` (default).
- `@AggregateIdentifier` field annotation removed; the `cardId` field stays plain. Identity now flows through `@EventTag` on events + `tagKey` on the entity.
- `@TargetAggregateIdentifier` → `@TargetEntityId` on every command field that targets the entity.
- `@EventTag(key = "GiftCard")` added on every event's id field — exactly one tag per event (no DCB).
- Creation command handler (the AF4 constructor): converted to **`static` `@CommandHandler` method**. A no-arg `@EntityCreator` constructor takes the place of the framework-only AF4 ctor.
- `AggregateLifecycle.apply(...)` calls → `eventAppender.append(...)` with `EventAppender` injected as the second parameter on every `@CommandHandler`. Static import of `apply` dropped.
- Imports: `org.axonframework.commandhandling.CommandHandler` → `org.axonframework.messaging.commandhandling.annotation.CommandHandler`; `org.axonframework.eventsourcing.EventSourcingHandler` → `org.axonframework.eventsourcing.annotation.EventSourcingHandler`.

## Caveats

- `tagKey` is project-specific. Pick the entity's simple class name and use it as the **same string** in `@EventSourced(tagKey=...)` and every event's `@EventTag(key=...)`.
- The AF4 framework-only no-arg constructor (`protected GiftCard()`) is replaced by the **public** `@EntityCreator` constructor. Drop the AF4 one — leaving both compiles but is dead code.
- If the AF4 `@Aggregate` carried `snapshotTriggerDefinition = "..."` or `cache = "..."`, those attributes are **not portable** to `@EventSourced`. Flag them under "Flagged for follow-up" — do not silently drop. Snapshotting must be re-wired separately if it was needed.
- If the id field is not `String` (e.g., a value-object `CardId`), add `idType = CardId.class` on `@EventSourced` — mismatched types fail at runtime, not compile time.
