# 05 — Multi-entity (`@AggregateMember` → `@EntityMember`)

**Why this case is interesting:** `@EntityMember` replaces `@AggregateMember` AND its semantics tighten in two important ways: (1) **`Map<K, V>` is NOT supported** — AF5 accepts `List<Value>` only; (2) the child entity drops `@EntityId` and is reached strictly through the parent (no class-level `@EventSourced` / `@EventSourcedEntity` on the child). Every event still carries exactly **one** `@EventTag` — keyed to the ROOT, never the child.

**Apply-condition:** scope contains at least one `@AggregateMember` field (any collection shape).

## Before (AF4) — `List<Transaction>` form (supported)

```java
import org.axonframework.modelling.command.AggregateMember;
import org.axonframework.modelling.command.EntityId;

@Aggregate
public class GiftCard {

    @AggregateIdentifier
    private String cardId;

    @AggregateMember
    private List<Transaction> transactions = new ArrayList<>();

    @CommandHandler
    public void handle(StartRedemptionCommand cmd) {
        apply(new RedemptionStartedEvent(cardId, cmd.transactionId(), cmd.amount()));
    }

    @EventSourcingHandler
    public void on(RedemptionStartedEvent evt) {
        this.transactions.add(new Transaction(evt.transactionId(), evt.amount()));
    }
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
```

## After (AF5) — `List<Transaction>` form

```java
import org.axonframework.modelling.entity.annotation.EntityMember;

@EventSourced(tagKey = "GiftCard")
public class GiftCard {

    private String cardId;

    @EntityMember(routingKey = "transactionId")             // ← key = child's id-property name
    private List<Transaction> transactions = new ArrayList<>();

    @EntityCreator
    public GiftCard() { }

    @CommandHandler
    public void handle(StartRedemptionCommand cmd, EventAppender appender) {
        appender.append(new RedemptionStartedEvent(cardId, cmd.transactionId(), cmd.amount()));
    }

    @EventSourcingHandler
    public void on(RedemptionStartedEvent evt) {
        this.transactions.add(new Transaction(evt.transactionId(), evt.amount()));
    }
}

public class Transaction {                                  // ← plain POJO, NO class-level annotation

    private String transactionId;                            // ← @EntityId removed, plain field
    private int amount;
    private boolean completed;

    public Transaction(String transactionId, int amount) {
        this.transactionId = transactionId;
        this.amount = amount;
    }

    @EntityCreator                                           // ← child also has @EntityCreator
    Transaction() { }

    @CommandHandler
    public void handle(CompleteRedemptionCommand cmd, EventAppender appender) {
        if (completed) throw new IllegalStateException("already completed");
        appender.append(new RedemptionCompletedEvent(cmd.cardId(), cmd.transactionId()));
    }

    @EventSourcingHandler
    public void on(RedemptionCompletedEvent evt) {
        this.completed = true;
    }
}

// Events — exactly ONE @EventTag per event, keyed to the ROOT (GiftCard).
public record RedemptionStartedEvent(@EventTag(key = "GiftCard") String cardId, String transactionId, int amount) { }
public record RedemptionCompletedEvent(@EventTag(key = "GiftCard") String cardId, String transactionId) { }
```

## What changed

- Field annotation: `@AggregateMember` → `@EntityMember(routingKey = "transactionId")`. The `routingKey` value MUST equal the child's id-field name — typos compile, route nothing, fail in tests.
- Import: `org.axonframework.modelling.command.AggregateMember` → `org.axonframework.modelling.entity.annotation.EntityMember`.
- Child class: `@EntityId` annotation + import removed; the id field stays plain.
- Child class is a plain POJO — **NO** `@EventSourced` / `@EventSourcedEntity` at class level. The framework wires it through the parent's `@EntityMember`.
- Child class carries `@EntityCreator` on a no-arg constructor (or another supported pattern — see use case 03). The parent's AF4 framework-only `protected Transaction()` no-arg gets `@EntityCreator`.
- Every `@CommandHandler` on the child takes `EventAppender` parameter; bodies use `appender.append(...)`.
- Events keep exactly **one** `@EventTag` — keyed to the ROOT (`"GiftCard"`), never to the child. Children don't have their own event stream without DCB.

## Blocker B1 — `Map<K, V>` form

If the AF4 source has `@AggregateMember Map<Key, Child>`:

```java
@AggregateMember
private Map<String, Transaction> transactionsById = new HashMap<>();
```

The recipe emits Blocker B1. The migration path documented in [multi-entity-migration.adoc](../../../docs/paths/aggregates/multi-entity-migration.adoc) ("Maps are not supported"): rewrite the field as `List<Value>` and manage id lookups internally OR via a custom resolver.

The rewrite is **not mechanical inside the recipe scope** because it touches:

- The parent's `@EventSourcingHandler` bodies that did `map.put(key, child)` / `map.remove(key)` — these become `list.add(...)` plus an explicit `list.removeIf(t -> t.txId().equals(key))` (or equivalent).
- Command handlers that did `map.get(key)` — these become a list scan with id-equality lookup, or a derived index field on the parent.
- Events' shape may need to change if the key was a synthetic id not previously emitted.
- **All readers / projections / tests outside the aggregate that observed the map shape** — `Map<K, V>` projections become `List<V>` ones, with all the breakage that implies.

Recipe-specific Option offered by the recipe alongside skip / revert / solve-manually:

- `redesign-map-to-list` — pause this item. Caller rewrites the `Map<K, V>` member as `List<V>` plus id-management logic, updates every reader/projection that observed the map, then re-invokes the skill. The recipe will then proceed via Step M with the standard `@EntityMember(routingKey = "<idProperty>") List<V>` mapping.

Example Blocker block:

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.example.inventory.Inventory`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** Blocker B1 (Map-typed @AggregateMember) fired at `Inventory.java:24` — `@AggregateMember private Map<String, StockItem> items`. AF5 `@EntityMember` supports `List<Value>` only (see [multi-entity-migration.adoc](../../../docs/paths/aggregates/multi-entity-migration.adoc) § "Maps are not supported"). Migration path: rewrite as `List<StockItem>` + internal id lookup (or custom resolver). The rewrite touches the parent's `@EventSourcingHandler` bodies (map put/remove → list ops), command-handler reads (`map.get(key)` → list scan), and every reader/projection that observed the map shape — all outside this recipe's scope.
>
> **Options:**
> - [ ] **skip** — leave `Inventory` in its current partial state; queue moves on.
> - [ ] **revert** — undo this recipe's edits; restore the pre-recipe `@AggregateMember Map<…>` shape.
> - [ ] **solve-manually** — pause; caller fixes by hand.
> - [ ] **redesign-map-to-list** — pause; caller rewrites the Map member as `List<V>` plus id-management logic, updates external readers/projections, then re-invokes with the new shape.
```

## Caveats

- **`routingKey` must exactly match the child's id-field name.** Typos route nothing; runtime-only failure. Test every child command after migration.
- **Never put `@EventTag` on a child class or a child-shape event.** Tags belong to the ROOT entity — one per event.
- **Never annotate the child with `@EventSourced` / `@EventSourcedEntity`.** AF5 wires children through `@EntityMember`; double-annotation throws "entity already registered" at startup.
- **Drop the AF4 framework-only no-arg ctor on the child** once `@EntityCreator` is on a usable constructor; leaving both is dead code that risks confusion.
- For the Map → List rewrite, do NOT preserve the original key as a `String key` field on the child if it duplicates an existing id field. Single source of truth: the child's id field is its identity.
