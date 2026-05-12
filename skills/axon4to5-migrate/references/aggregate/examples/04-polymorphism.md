# 04 — Polymorphic aggregate (AutoDetected)

**Why this case is interesting:** Abstract base + two concrete subtypes
inheriting `@CommandHandler` / `@EventSourcingHandler` methods. AF4 wires the
hierarchy through subclass `@Aggregate` stereotypes + an explicit
`AggregateConfigurer.withSubtypes(...)` (or Spring auto-detection). AF5
declares the subtypes on the **base** via `concreteTypes = {…}` —
subtypes drop their class-level stereotype entirely. The Declarative path
(`EventSourcedEntityModule.declarative(...)`) is out of scope for the
architecture-neutral migration.

**Variant:** polymorphic

## Before (AF4)

```java
package com.example.giftcard;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.TargetAggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

// Spring auto-detection picks up the abstract base AND the subclasses
// because all three carry @Aggregate. (Core projects would use
// AggregateConfigurer.defaultConfiguration(GiftCard.class)
//                    .withSubtypes(OpenLoopGiftCard.class, RechargeableGiftCard.class)
// in their AxonConfig.)
@Aggregate
public abstract class GiftCard {

    @AggregateIdentifier
    protected String cardId;
    protected int remainingValue;

    @CommandHandler
    public void handle(RedeemCardCommand cmd) {
        if (cmd.amount() > remainingValue) throw new IllegalStateException("insufficient");
        apply(new CardRedeemedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler
    public void on(CardRedeemedEvent evt) {
        this.remainingValue -= evt.amount();
    }

    protected GiftCard() { /* required by AF4 */ }
}

@Aggregate
public class OpenLoopGiftCard extends GiftCard {

    @CommandHandler
    public OpenLoopGiftCard(IssueOpenLoopCardCommand cmd) {
        apply(new OpenLoopCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @EventSourcingHandler
    public void on(OpenLoopCardIssuedEvent evt) {
        this.cardId = evt.cardId();
        this.remainingValue = evt.amount();
    }

    protected OpenLoopGiftCard() { }
}

@Aggregate
public class RechargeableGiftCard extends GiftCard {

    @CommandHandler
    public RechargeableGiftCard(IssueRechargeableCardCommand cmd) {
        apply(new RechargeableCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @CommandHandler
    public void handle(RechargeCardCommand cmd) {
        apply(new CardRechargedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler
    public void on(RechargeableCardIssuedEvent evt) {
        this.cardId = evt.cardId();
        this.remainingValue = evt.amount();
    }

    @EventSourcingHandler
    public void on(CardRechargedEvent evt) {
        this.remainingValue += evt.amount();
    }

    protected RechargeableGiftCard() { }
}
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

// tagKey + concreteTypes live on the BASE only. Subtypes inherit tagKey.
@EventSourced(
        tagKey = "GiftCard",
        concreteTypes = { OpenLoopGiftCard.class, RechargeableGiftCard.class }
)
public abstract class GiftCard {

    protected String cardId;
    protected int remainingValue;

    @EntityCreator
    protected GiftCard() { }

    @CommandHandler
    public void handle(RedeemCardCommand cmd, EventAppender eventAppender) {
        if (cmd.amount() > remainingValue) throw new IllegalStateException("insufficient");
        eventAppender.append(new CardRedeemedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler
    public void on(CardRedeemedEvent evt) {
        this.remainingValue -= evt.amount();
    }
}

// NO class-level stereotype on subtypes — discovered via base's concreteTypes.
public class OpenLoopGiftCard extends GiftCard {

    @EntityCreator
    public OpenLoopGiftCard() { }

    @CommandHandler
    public static void handle(IssueOpenLoopCardCommand cmd, EventAppender eventAppender) {
        eventAppender.append(new OpenLoopCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @EventSourcingHandler
    public void on(OpenLoopCardIssuedEvent evt) {
        this.cardId = evt.cardId();
        this.remainingValue = evt.amount();
    }
}

public class RechargeableGiftCard extends GiftCard {

    @EntityCreator
    public RechargeableGiftCard() { }

    @CommandHandler
    public static void handle(IssueRechargeableCardCommand cmd, EventAppender eventAppender) {
        eventAppender.append(new RechargeableCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @CommandHandler
    public void handle(RechargeCardCommand cmd, EventAppender eventAppender) {
        eventAppender.append(new CardRechargedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler
    public void on(RechargeableCardIssuedEvent evt) {
        this.cardId = evt.cardId();
        this.remainingValue = evt.amount();
    }

    @EventSourcingHandler
    public void on(CardRechargedEvent evt) {
        this.remainingValue += evt.amount();
    }
}

// Commands
public record IssueOpenLoopCardCommand(String cardId, int amount) { }
public record IssueRechargeableCardCommand(String cardId, int amount) { }
public record RedeemCardCommand(@TargetEntityId String cardId, int amount) { }
public record RechargeCardCommand(@TargetEntityId String cardId, int amount) { }

// Events — tagged to the BASE's tagKey ("GiftCard"), regardless of which
// subtype emitted them. One @EventTag per event.
public record OpenLoopCardIssuedEvent(@EventTag(key = "GiftCard") String cardId, int amount) { }
public record RechargeableCardIssuedEvent(@EventTag(key = "GiftCard") String cardId, int amount) { }
public record CardRechargedEvent(@EventTag(key = "GiftCard") String cardId, int amount) { }
public record CardRedeemedEvent(@EventTag(key = "GiftCard") String cardId, int amount) { }
```

For a **core (non-Spring)** project, replace `@EventSourced` with
`@EventSourcedEntity` on the base and register the hierarchy once:

```java
configurer.registerEntity(
        EventSourcedEntityModule.autodetected(String.class, GiftCard.class)
);
// Remove the AF4 AggregateConfigurer.defaultConfiguration(GiftCard.class).withSubtypes(...) call.
```

## What changed

- See [`polymorphism-migration.md`](../polymorphism-migration.md) for the full procedure (AutoDetected path).
- **Base class** carries the entity stereotype with `concreteTypes` listing every subtype:
  `@EventSourced(tagKey = "GiftCard", concreteTypes = { OpenLoopGiftCard.class, RechargeableGiftCard.class })`
  (core: `@EventSourcedEntity(...)`).
- **`tagKey` lives on the base only.** Subtypes inherit it; do not redeclare. Every event from any subtype still carries one `@EventTag(key = "GiftCard")`.
- **Subtypes drop the class-level `@Aggregate` stereotype.** They are discovered through the base's `concreteTypes` — double-annotating produces "entity already registered".
- All `@AggregateIdentifier` annotations removed; the protected `cardId` field stays as plain state.
- All `@CommandHandler` / `@EventSourcingHandler` imports moved to AF5 packages on **both** the base and every subtype.
- Subtype constructor command handlers → **`static` `@CommandHandler` methods** + no-arg `@EntityCreator` constructor on each subtype (creation handlers default to the `ALWAYS` row of the creation-policy matrix).
- Every `apply(...)` rewritten to `eventAppender.append(...)` with `EventAppender` injected as a parameter.
- Core only: AF4 `AggregateConfigurer.defaultConfiguration(GiftCard.class).withSubtypes(...)` → `EventSourcedEntityModule.autodetected(String.class, GiftCard.class)` — registered once on the base. (That call usually lives in a separate config class — out of scope for this skill; flag it.)

## Caveats

- **Subtypes MUST NOT carry `@EventSourced` / `@EventSourcedEntity`.** AF5 discovers them through the base's `concreteTypes`; redundant stereotypes throw at startup.
- **Subtypes MUST extend the migrated base.** A subtype that still extends an AF4-shaped base (or one that lost its annotation by mistake) will simply not be discovered.
- **`concreteTypes` MUST list every concrete subtype.** Missing entries surface as commands routed to the base instead of the intended subtype — runtime failures, not compile errors. Verify by running the test class for **every** subtype.
- **Do NOT migrate to `EventSourcedEntityModule.declarative(...)`** unless the project explicitly needs metamodel overrides. AutoDetected is the architecture-neutral path.
- **Do NOT put `concreteTypes` on a non-abstract base.** The mechanism is for hierarchy roots; if the AF4 base was concrete, checkpoint with the user before forcing it abstract.
- **`@EntityCreator` placement.** Both base AND each subtype carry one. The base's is `protected` and exists for the framework's no-arg path; each subtype's is `public` and supports its own creation command.
