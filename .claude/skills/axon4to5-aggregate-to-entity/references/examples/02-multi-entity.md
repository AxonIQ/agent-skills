# Multi-entity aggregate, Spring Boot → spring-boot

Observable shape that triggers this variant:

- Root class annotated with `@Aggregate` / `@AggregateRoot`.
- At least one field annotated `@AggregateMember`, holding a
  `List<ChildEntity>`.
- Child class has an `@EntityId` field; child class has its own
  `@CommandHandler` and/or `@EventSourcingHandler` methods.

AF4 source flavor: Spring Boot
AF5 target flavor (`--configuration-mode`): `spring-boot`

## Before (Java)

```java
import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.AggregateMember;
import org.axonframework.modelling.command.EntityId;
import org.axonframework.spring.stereotype.Aggregate;

import java.util.ArrayList;
import java.util.List;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
public class GiftCard {

    @AggregateIdentifier
    private String cardId;

    @AggregateMember
    private List<Transaction> transactions = new ArrayList<>();

    public GiftCard() {
    }

    @CommandHandler
    public GiftCard(IssueCardCommand cmd) {
        apply(new CardIssuedEvent(cmd.getCardId(), cmd.getAmount()));
    }

    @CommandHandler
    public void handle(RedeemCardCommand cmd) {
        apply(new CardRedeemedEvent(cardId, cmd.getAmount(), cmd.getTransactionId()));
    }

    @EventSourcingHandler
    public void on(CardIssuedEvent event) {
        this.cardId = event.getCardId();
    }

    @EventSourcingHandler
    public void on(CardRedeemedEvent event) {
        this.transactions.add(new Transaction(event.getTransactionId(), event.getAmount()));
    }
}

class Transaction {

    @EntityId
    private String transactionId;
    private int amount;

    public Transaction(String transactionId, int amount) {
        this.transactionId = transactionId;
        this.amount = amount;
    }
}
```

## After (Java)

```java
import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.extension.spring.stereotype.EventSourced;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;
import org.axonframework.modelling.entity.annotation.EntityMember;

import java.util.ArrayList;
import java.util.List;

@EventSourced
public class GiftCard {

    private String cardId;

    @EntityMember(routingKey = "transactionId")
    private List<Transaction> transactions = new ArrayList<>();

    @EntityCreator
    public GiftCard() {
    }

    @CommandHandler
    public static void handle(IssueCardCommand cmd, EventAppender appender) {
        appender.append(new CardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @CommandHandler
    public void handle(RedeemCardCommand cmd, EventAppender appender) {
        appender.append(new CardRedeemedEvent(cardId, cmd.amount(), cmd.transactionId()));
    }

    @EventSourcingHandler
    public void on(CardIssuedEvent event) {
        this.cardId = event.cardId();
    }

    @EventSourcingHandler
    public void on(CardRedeemedEvent event) {
        this.transactions.add(new Transaction(event.transactionId(), event.amount()));
    }
}

class Transaction {

    private String transactionId;
    private int amount;

    public Transaction(String transactionId, int amount) {
        this.transactionId = transactionId;
        this.amount = amount;
    }
}
```

## Notes

- `@AggregateMember` → `@EntityMember(routingKey = "transactionId")`.
  The routing key is **always** required when the AF4 form relied on
  per-child routing (which it does whenever `@EntityId` was present on
  the child).
- `@EntityId` removed from `Transaction.transactionId`. The field name
  itself drives routing because it matches `routingKey`.
- `Transaction` does **not** get a class-level `@EventSourced` /
  `@EventSourcedEntity` annotation — it is a child entity, not an
  event-sourced root.
- `Map<Key, Value>` for child entities is **not supported** by
  `@EntityMember`. If the AF4 code uses a Map, the skill must stop and
  ask the human before continuing (it changes domain semantics to
  silently rewrite that into a List).
