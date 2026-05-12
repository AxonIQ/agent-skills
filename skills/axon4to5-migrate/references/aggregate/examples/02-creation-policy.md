# 02 — `@CreationPolicy(CREATE_IF_MISSING)`

**Why this case is interesting:** The highest-risk row of the decision
table — wrong static-vs-instance choice **compiles cleanly** and fails only
at runtime / test time (`EntityAlreadyExistsForCreationalCommandHandlerException`
or a silent overwrite). Shows the production code AND the test that
distinguishes `CREATE_IF_MISSING` (create-or-update) from `ALWAYS`
(create-only-when-missing).

**Variant:** creation-policy

## Before (AF4)

```java
package com.example.giftcard;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateCreationPolicy;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.CreationPolicy;
import org.axonframework.modelling.command.TargetAggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
public class GiftCard {

    @AggregateIdentifier
    private String cardId;
    private int remainingValue;

    // ALWAYS — must NOT collide with an existing entity
    @CommandHandler
    @CreationPolicy(AggregateCreationPolicy.ALWAYS)
    public void handle(IssueCardCommand cmd) {
        apply(new CardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    // CREATE_IF_MISSING — create-or-update, same handler in both cases
    @CommandHandler
    @CreationPolicy(AggregateCreationPolicy.CREATE_IF_MISSING)
    public void handle(IssueOrTopUpCommand cmd) {
        apply(new CardToppedUpEvent(cmd.cardId(), cmd.amount()));
    }

    // NEVER (or absent) — default: must already exist
    @CommandHandler
    @CreationPolicy(AggregateCreationPolicy.NEVER)
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
    public void on(CardToppedUpEvent evt) {
        this.cardId = evt.cardId();
        this.remainingValue += evt.amount();
    }

    @EventSourcingHandler
    public void on(CardRedeemedEvent evt) {
        this.remainingValue -= evt.amount();
    }

    protected GiftCard() { /* required by AF4 */ }
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

@EventSourced(tagKey = "GiftCard")
public class GiftCard {

    private String cardId;
    private int remainingValue;

    @EntityCreator
    public GiftCard() { }

    // ALWAYS → static @CommandHandler. Framework throws
    // EntityAlreadyExistsForCreationalCommandHandlerException on collision.
    @CommandHandler
    public static void handle(IssueCardCommand cmd, EventAppender eventAppender) {
        eventAppender.append(new CardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    // CREATE_IF_MISSING → instance @CommandHandler + no-arg @EntityCreator.
    // Framework materialises an empty entity on first invocation; the same
    // handler runs whether the entity is new or existing.
    @CommandHandler
    public void handle(IssueOrTopUpCommand cmd, EventAppender eventAppender) {
        eventAppender.append(new CardToppedUpEvent(cmd.cardId(), cmd.amount()));
    }

    // NEVER → instance @CommandHandler (default — no annotation needed).
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
    public void on(CardToppedUpEvent evt) {
        this.cardId = evt.cardId();
        this.remainingValue += evt.amount();
    }

    @EventSourcingHandler
    public void on(CardRedeemedEvent evt) {
        this.remainingValue -= evt.amount();
    }
}

// Commands
public record IssueCardCommand(String cardId, int amount) { }
public record IssueOrTopUpCommand(@TargetEntityId String cardId, int amount) { }
public record RedeemCardCommand(@TargetEntityId String cardId, int amount) { }

// Events
public record CardIssuedEvent(@EventTag(key = "GiftCard") String cardId, int amount) { }
public record CardToppedUpEvent(@EventTag(key = "GiftCard") String cardId, int amount) { }
public record CardRedeemedEvent(@EventTag(key = "GiftCard") String cardId, int amount) { }
```

## Distinguishing test (the only signal that catches the wrong row)

```java
import org.axonframework.eventsourcing.configuration.EventSourcingConfigurer;
import org.axonframework.test.fixture.AxonTestFixture;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

class GiftCardCreationPolicyTest {

    private final AxonTestFixture fixture = AxonTestFixture.with(
            EventSourcingConfigurer.create()
                    .registerEntity(/* … see test-fixture-mapping.md … */)
    );

    @AfterEach
    void tearDown() { fixture.stop(); }

    // ALWAYS — second IssueCardCommand for the same id must fail.
    @Test
    void issueTwice_throws() {
        fixture.given()
                .events(new CardIssuedEvent("card-1", 100))
                .when()
                .command(new IssueCardCommand("card-1", 50))
                .then()
                // domain-level: EntityAlreadyExistsForCreationalCommandHandlerException
                .exception(Exception.class);
    }

    // CREATE_IF_MISSING — top-up against a non-existent card creates it.
    @Test
    void topUp_onMissingCard_creates() {
        fixture.given()
                .noPriorActivity()
                .when()
                .command(new IssueOrTopUpCommand("card-2", 30))
                .then()
                .events(new CardToppedUpEvent("card-2", 30));
    }

    // CREATE_IF_MISSING — top-up against an existing card updates it.
    @Test
    void topUp_onExistingCard_updates() {
        fixture.given()
                .events(new CardIssuedEvent("card-3", 100))
                .when()
                .command(new IssueOrTopUpCommand("card-3", 40))
                .then()
                .events(new CardToppedUpEvent("card-3", 40));
    }
}
```

## What changed

- See [`creation-policy-decision.md`](../creation-policy-decision.md) for the full decision matrix and the NPE-on-null-state gotcha.
- `@CreationPolicy(ALWAYS)` → **`static` `@CommandHandler` method**. The framework's `EntityAlreadyExistsForCreationalCommandHandlerException` replaces the AF4 implicit "constructor command" semantics.
- `@CreationPolicy(CREATE_IF_MISSING)` → **instance `@CommandHandler` + no-arg `@EntityCreator`**. The instance handler runs against a freshly-materialised entity on first invocation. (Doc-aligned alternative: `static` handler + `@InjectEntity @Nullable` — only when the AF4 code already threw on existing entities. See `creation-policy-decision.md`.)
- `@CreationPolicy(NEVER)` → **instance `@CommandHandler`** (default). No annotation needed.
- All three `CreationPolicy` / `AggregateCreationPolicy` imports removed. The annotation is **dead code** in AF5 — do not keep it as a comment.

## Caveats

- **No compile-time signal.** Picking the wrong shape compiles cleanly. The test class is the only reliable check — run it after every `@CreationPolicy` migration.
- **`CREATE_IF_MISSING` NPE gotcha.** AF5 always materialises an empty entity for instance handlers, so the handler now runs on `this` with all fields `null` / `0` / `false`. If the AF4 handler implicitly relied on `AggregateNotFoundException`, the AF5 handler enters the body and NPEs on the first method call against a null field. Two fixes: (1) add a domain-level guard at the top of the handler (`if (this.cardId == null) throw new …`), or (2) update the test expectation from `AggregateNotFoundException` to the actual domain exception.
- **Never reflex-make every creation handler `static`.** That collapses `CREATE_IF_MISSING` into `ALWAYS` and breaks create-or-update flows.
- **AF4 `AggregateNotFoundException` is not the AF5 equivalent of "no entity yet".** AF5 instance handlers run on an empty entity; tests asserting that exception must be relaxed (see [`test-fixture-mapping.md`](../test-fixture-mapping.md)).
