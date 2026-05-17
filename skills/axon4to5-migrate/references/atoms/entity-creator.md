---
atom-id: entity-creator
title: "@EntityCreator — annotate the no-arg constructor"
af4-symbols: ["(implicit no-arg constructor)"]
af5-symbols: ["@EntityCreator", "org.axonframework.eventsourcing.annotation.reflection.EntityCreator"]
detect: class annotated @EventSourced/@EventSourcedEntity without @EntityCreator on any constructor
used-by: [aggregate]
---

# @EntityCreator — Annotate the No-Arg Constructor

AF4 used an implicit no-arg constructor to materialise an empty aggregate before replaying events. AF5 requires the
`@EntityCreator` annotation to be **explicitly** placed on the constructor that creates the empty entity shell.

## Detect

```bash
# Find aggregates missing @EntityCreator
grep -rln '@EventSourced\|@EventSourcedEntity' --include='*.java' . \
  | xargs grep -rL '@EntityCreator'
```

## Before (AF4)

```java
@Aggregate
public class Order {
    public Order() {}   // implicit — framework used this automatically
}
```

## After (AF5)

```java
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;

@EventSourced(tagKey = "Order", idType = OrderId.class)
public class Order {

    @EntityCreator
    public Order() {}
}
```

## Import

`org.axonframework.eventsourcing.annotation.reflection.EntityCreator`

⚠️ The **`.reflection.`** infix is mandatory — `org.axonframework.eventsourcing.annotation.EntityCreator` does not
exist. This is the single most-common import mistake for this annotation.

## Rules

- At least **one** constructor per class must carry `@EntityCreator`.
- For **polymorphic aggregates**, each **concrete subtype** needs its own `@EntityCreator` constructor; the abstract
  base does not need it (AF5 materialises the correct subtype via `concreteTypes`).
- For **multi-entity child entities** (`@EntityMember`), each child entity class also needs `@EntityCreator` on its
  own constructor.
- If there is no explicit no-arg constructor (only a parameterised one), add a no-arg constructor and annotate it —
  unless the creation pattern is "ALWAYS" (`@CreationPolicy(ALWAYS)` → static `@CommandHandler`), in which case
  `@EntityCreator` on a no-arg constructor is still needed for the empty shell before sourcing.

## Gotchas

- **OpenRewrite Phase 1 often adds `@EntityCreator`** already. Grep before adding to avoid a duplicate annotation
  that compiles but signals partial state to reviewers.
- **Missing `.reflection.` infix** — the most common mistake. `javac` gives `cannot find symbol` on `@EntityCreator`
  if the import is from the wrong package.
- **`@EntityCreator` is NOT the creational command handler** — it annotates the shell constructor, not the
  `@CommandHandler` that handles the first command. Those are separate methods.

## AF5 Exception Flip (related)

With `@EntityCreator` on a no-arg constructor, AF5 materialises an **empty entity** and runs an instance
`@CommandHandler` even if no entity exists yet. AF4 would have thrown `AggregateNotFoundException`. Any project
domain rule against empty state (e.g., `if (state == null) throw new DomainException(…)`) fires instead.
Tests that expected `AggregateNotFoundException` must flip to the project's domain exception. See
`aggregate/RECIPE.md` § Gotchas "AF5 exception flips".

## Used By

- **[[aggregate]]** — common steps (always), Step 3 "Aggregate body"
- **[[entity-member]]** — child entities within a multi-entity aggregate also need `@EntityCreator`
