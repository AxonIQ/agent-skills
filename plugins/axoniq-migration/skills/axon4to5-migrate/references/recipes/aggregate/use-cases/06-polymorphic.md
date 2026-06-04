# 06 — Polymorphic aggregate hierarchy (`concreteTypes`)

**Why this case is interesting:** AF4 wires a polymorphic hierarchy through subclass `@Aggregate` stereotypes (Spring auto-detect) OR `AggregateConfigurer.withSubtypes(...)` (native). AF5 inverts this: **the base** carries `@EventSourcedEntity(concreteTypes = {Sub1.class, ...})` and subtypes drop their class-level stereotype entirely. Double-annotation throws "entity already registered" at startup.

**Apply-condition:** `$SOURCE` is abstract `@AggregateRoot` (or `@Aggregate`) with concrete `@Aggregate` subclasses in the same module.

## Before (AF4)

```java
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.AggregateRoot;
import org.axonframework.spring.stereotype.Aggregate;
import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@AggregateRoot                                                  // ← abstract base also annotated
public abstract class Card {

    @AggregateIdentifier
    protected String cardId;
    protected int balance;

    @CommandHandler
    public void handle(DebitCardCommand cmd) {
        if (cmd.amount() > balance) throw new IllegalStateException("insufficient");
        apply(new CardDebitedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler
    public void on(CardDebitedEvent e) {
        this.balance -= e.amount();
    }

    Card() { }
}

@Aggregate                                                       // ← subtype carries its own stereotype
public class OpenLoopGiftCard extends Card {

    @CommandHandler
    public OpenLoopGiftCard(IssueOpenLoopCommand cmd) {
        apply(new OpenLoopCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @EventSourcingHandler
    void on(OpenLoopCardIssuedEvent e) {
        this.cardId = e.cardId();
        this.balance = e.amount();
    }

    OpenLoopGiftCard() { }
}

@Aggregate
public class RechargeableGiftCard extends Card {

    @CommandHandler
    public RechargeableGiftCard(IssueRechargeableCommand cmd) {
        apply(new RechargeableCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @CommandHandler
    public void handle(RechargeCommand cmd) {
        apply(new CardRechargedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler void on(RechargeableCardIssuedEvent e) { this.cardId = e.cardId(); this.balance = e.amount(); }
    @EventSourcingHandler void on(CardRechargedEvent e)            { this.balance += e.amount(); }

    RechargeableGiftCard() { }
}
```

Plus, for native projects, somewhere in the bootstrap:

```java
AggregateConfigurer.defaultConfiguration(Card.class)
    .withSubtypes(OpenLoopGiftCard.class, RechargeableGiftCard.class);
```

## After (AF5) — native path (Path B)

```java
@EventSourcedEntity(
        tagKey = "Card",
        idType = String.class,
        concreteTypes = { OpenLoopGiftCard.class, RechargeableGiftCard.class }   // ← lives on the BASE only
)
public abstract class Card {

    protected String cardId;
    protected int balance;

    @EntityCreator
    protected Card() { }

    @CommandHandler
    public void handle(DebitCardCommand cmd, EventAppender appender) {
        if (cmd.amount() > balance) throw new IllegalStateException("insufficient");
        appender.append(new CardDebitedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler
    public void on(CardDebitedEvent e) {
        this.balance -= e.amount();
    }
}

// NO class-level @EventSourcedEntity on subtypes — discovered via base's concreteTypes.
public class OpenLoopGiftCard extends Card {

    @EntityCreator
    public OpenLoopGiftCard() { }

    @CommandHandler
    public static void handle(IssueOpenLoopCommand cmd, EventAppender appender) {
        appender.append(new OpenLoopCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @EventSourcingHandler
    void on(OpenLoopCardIssuedEvent e) {
        this.cardId = e.cardId();
        this.balance = e.amount();
    }
}

public class RechargeableGiftCard extends Card {

    @EntityCreator
    public RechargeableGiftCard() { }

    @CommandHandler
    public static void handle(IssueRechargeableCommand cmd, EventAppender appender) {
        appender.append(new RechargeableCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @CommandHandler
    public void handle(RechargeCommand cmd, EventAppender appender) {
        appender.append(new CardRechargedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler void on(RechargeableCardIssuedEvent e) { this.cardId = e.cardId(); this.balance = e.amount(); }
    @EventSourcingHandler void on(CardRechargedEvent e)            { this.balance += e.amount(); }
}
```

Bootstrap (native — Path B):

```java
configurer.registerEntity(
        EventSourcedEntityModule.autodetected(String.class, Card.class)         // ← registered ONCE on the base
);
// Delete the AF4 AggregateConfigurer.defaultConfiguration(Card.class).withSubtypes(...) call.
```

For Spring (Path A), substitute `@EventSourced(...)` for `@EventSourcedEntity(...)` on the base; bootstrap registration is auto-discovered.

## What changed

- **Base class**: `@AggregateRoot` (or `@Aggregate`) → `@EventSourcedEntity(tagKey = "...", idType = ..., concreteTypes = { Sub1.class, Sub2.class })` (Path B) OR `@EventSourced(...)` (Path A).
- **Subtypes**: class-level `@Aggregate` annotation removed entirely. Subtypes carry NO stereotype — discovered via `concreteTypes`.
- `tagKey` lives on the **base** only. Subtypes inherit it. Every event from any subtype still carries `@EventTag(key = "<base tagKey>")` — one tag per event.
- `@AggregateIdentifier` removed from the base; protected id field stays plain.
- Every `@CommandHandler` / `@EventSourcingHandler` import moves to AF5 packages — on **both** the base AND every subtype.
- Subtype creation handlers (constructor-style) → **static** `@CommandHandler` factories. The base has a `protected @EntityCreator` no-arg constructor for the framework; each subtype has a `public @EntityCreator` constructor too.
- Native bootstrap: `AggregateConfigurer.defaultConfiguration(Base.class).withSubtypes(...)` → `EventSourcedEntityModule.autodetected(IdType.class, Base.class)`. Single registration on the base.

## Caveats

- **Subtypes MUST NOT carry `@EventSourced` / `@EventSourcedEntity`.** Double-annotation throws "entity already registered" at startup.
- **`concreteTypes` MUST list every concrete subtype.** Missing entries surface as commands routed to the base instead of the intended subtype — runtime failure, no compile signal.
- **Subtypes MUST extend the migrated base.** A subtype still extending an AF4-shaped base (or one that lost its annotation by mistake) simply isn't discovered.
- **DO NOT migrate to `EventSourcedEntityModule.declarative(...)`** unless the project explicitly needs metamodel overrides. AutoDetected is the architecture-neutral path.
- **DO NOT force a concrete base abstract.** If the AF4 base was non-abstract, checkpoint with the user — making it abstract is a behavioural change.
- **`@EntityCreator` lives on both** the base (protected, framework-only no-arg) AND each subtype (public, supports the subtype's creation command). Forgetting either causes startup failure or routing failure.
