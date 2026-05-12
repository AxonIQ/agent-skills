# 03 — Multi-entity aggregate

**Why this case is interesting:** `@AggregateMember` (parent) → `@EntityMember(routingKey="…")`,
plus `@EntityId` removal on the child. Shows the **`List<Child>`** form
(the supported shape). The **`Map<K, Child>`** form is a breaking change
in AF5 — `@EntityMember` only supports `List`; document any Map-based AF4
case in a separate sibling file (e.g. `03b-multi-entity-map.md`) so the
re-modelling is explicit.

**Variant:** multi-entity, Spring

## Before (AF4)

```java
package com.example.giftcard;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.AggregateMember;
import org.axonframework.modelling.command.EntityId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;

import java.util.ArrayList;
import java.util.List;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
public class GiftCard {

    @AggregateIdentifier
    private String cardId;
    private int remainingValue;

    @AggregateMember
    private List<Transaction> transactions = new ArrayList<>();

    @CommandHandler
    public GiftCard(IssueCardCommand cmd) {
        apply(new CardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @CommandHandler
    public void handle(StartRedemptionCommand cmd) {
        if (cmd.amount() > remainingValue) throw new IllegalStateException("insufficient");
        apply(new RedemptionStartedEvent(cardId, cmd.transactionId(), cmd.amount()));
    }

    @EventSourcingHandler
    public void on(CardIssuedEvent evt) {
        this.cardId = evt.cardId();
        this.remainingValue = evt.amount();
    }

    @EventSourcingHandler
    public void on(RedemptionStartedEvent evt) {
        this.remainingValue -= evt.amount();
        this.transactions.add(new Transaction(evt.transactionId(), evt.amount()));
    }

    protected GiftCard() { /* required by AF4 */ }
}

public class Transaction {

    @EntityId
    private String transactionId;
    private int amount;
    private boolean completed;

    public Transaction(String transactionId, int amount) {
        this.transactionId = transactionId;
        this.amount = amount;
    }

    @CommandHandler
    public void handle(CompleteRedemptionCommand cmd) {
        if (completed) throw new IllegalStateException("already completed");
        apply(new RedemptionCompletedEvent(cmd.cardId(), cmd.transactionId()));
    }

    @EventSourcingHandler
    public void on(RedemptionCompletedEvent evt) {
        this.completed = true;
    }

    protected Transaction() { }
}

// Commands
public record IssueCardCommand(String cardId, int amount) { }
public record StartRedemptionCommand(@TargetAggregateIdentifier String cardId, String transactionId, int amount) { }
public record CompleteRedemptionCommand(@TargetAggregateIdentifier String cardId, String transactionId) { }
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
import org.axonframework.modelling.entity.annotation.EntityMember;

import java.util.ArrayList;
import java.util.List;

@EventSourced(tagKey = "GiftCard")
public class GiftCard {

    private String cardId;
    private int remainingValue;

    @EntityMember(routingKey = "transactionId")
    private List<Transaction> transactions = new ArrayList<>();

    @EntityCreator
    public GiftCard() { }

    @CommandHandler
    public static void handle(IssueCardCommand cmd, EventAppender eventAppender) {
        eventAppender.append(new CardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @CommandHandler
    public void handle(StartRedemptionCommand cmd, EventAppender eventAppender) {
        if (cmd.amount() > remainingValue) throw new IllegalStateException("insufficient");
        eventAppender.append(new RedemptionStartedEvent(cardId, cmd.transactionId(), cmd.amount()));
    }

    @EventSourcingHandler
    public void on(CardIssuedEvent evt) {
        this.cardId = evt.cardId();
        this.remainingValue = evt.amount();
    }

    @EventSourcingHandler
    public void on(RedemptionStartedEvent evt) {
        this.remainingValue -= evt.amount();
        this.transactions.add(new Transaction(evt.transactionId(), evt.amount()));
    }
}

public class Transaction {

    private String transactionId; // plain field — no @EntityId in AF5
    private int amount;
    private boolean completed;

    public Transaction(String transactionId, int amount) {
        this.transactionId = transactionId;
        this.amount = amount;
    }

    @CommandHandler
    public void handle(CompleteRedemptionCommand cmd, EventAppender eventAppender) {
        if (completed) throw new IllegalStateException("already completed");
        eventAppender.append(new RedemptionCompletedEvent(cmd.cardId(), cmd.transactionId()));
    }

    @EventSourcingHandler
    public void on(RedemptionCompletedEvent evt) {
        this.completed = true;
    }
}

// Commands
public record IssueCardCommand(String cardId, int amount) { }
public record StartRedemptionCommand(@TargetEntityId String cardId, String transactionId, int amount) { }
public record CompleteRedemptionCommand(@TargetEntityId String cardId, String transactionId) { }

// Events — exactly ONE @EventTag per event, keyed to the ROOT entity (GiftCard).
// Child tagging is NOT a thing without DCB.
public record CardIssuedEvent(@EventTag(key = "GiftCard") String cardId, int amount) { }
public record RedemptionStartedEvent(@EventTag(key = "GiftCard") String cardId, String transactionId, int amount) { }
public record RedemptionCompletedEvent(@EventTag(key = "GiftCard") String cardId, String transactionId) { }
```

## What changed

- See [`multi-entity-migration.md`](../multi-entity-migration.md) for the full procedure.
- Parent field: `@AggregateMember List<Transaction>` → `@EntityMember(routingKey = "transactionId") List<Transaction>`. The `routingKey` value is the **child's id-field name** — it must match the field whose value the command's `@TargetEntityId`-resolved id is routed to.
- Import swap: `org.axonframework.modelling.command.AggregateMember` → `org.axonframework.modelling.entity.annotation.EntityMember`.
- Child: `@EntityId` annotation + import removed. The child's id field stays as a plain field; AF5 has no annotation requirement for it.
- Child remains a **plain POJO** — do NOT add `@EventSourced` / `@EventSourcedEntity` to it. The parent's `@EntityMember` wires it.
- Tagging: every event still carries exactly **one** `@EventTag(key = "GiftCard")` — keyed to the ROOT (`GiftCard`), not the child. Children don't have their own event stream; they are state inside the parent, reconstructed by the parent's `@EventSourcingHandler`s.
- Child handlers (`@CommandHandler` / `@EventSourcingHandler`) get the same FQN swap as parent handlers.
- Child handler that previously called `apply(...)` now takes `EventAppender eventAppender` as a parameter and calls `eventAppender.append(...)`.

## Caveats

- **`Map<K, V>` is a breaking change.** `@EntityMember` does **not** support `Map`. If the AF4 source uses `@AggregateMember Map<Key, Transaction> by­Id`, you must re-model to `List<Transaction>` plus an id-bearing field. This is **not mechanical** — checkpoint with the user before doing it, and update every reader (handlers, projections, tests). Surface a Map-based child under "Flagged for follow-up" if the user opts out.
- **`routingKey` value is critical.** It must exactly match the child's id-field name (`transactionId` in this example). A typo compiles but routes nothing — tests catch it, the compiler doesn't.
- **Never put `@EventTag` on a child entity or on a child event.** Tags belong to the **root** — one per event.
- **Never annotate the child with `@EventSourced` / `@EventSourcedEntity`.** The framework wires children through `@EntityMember`; double-annotating produces "entity already registered" errors.
- The child's framework-only no-arg constructor (AF4 `protected Transaction()`) is no longer needed in AF5 if there is a usable ctor for the parent's `@EventSourcingHandler` to invoke (e.g. `new Transaction(id, amount)`). Drop it.
