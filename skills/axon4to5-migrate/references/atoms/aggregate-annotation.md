---
atom-id: aggregate-annotation
title: "Class stereotype — @Aggregate / @AggregateRoot → @EventSourced / @EventSourcedEntity"
af4-symbols: ["@Aggregate", "@AggregateRoot", "org.axonframework.spring.stereotype.Aggregate", "org.axonframework.modelling.command.AggregateRoot"]
af5-symbols: ["@EventSourced", "@EventSourcedEntity", "org.axonframework.extension.spring.stereotype.EventSourced", "org.axonframework.eventsourcing.annotation.EventSourcedEntity"]
detect: grep -rn '@Aggregate\|@AggregateRoot' --include='*.java' --include='*.kt' --include='*.scala' .
used-by: [aggregate]
---

# Class Stereotype: @Aggregate / @AggregateRoot → @EventSourced / @EventSourcedEntity

AF4 marked event-sourced aggregates with `@Aggregate` (Spring) or `@AggregateRoot` (native configurer). AF5 renames
both and requires **explicit** `tagKey` and `idType` on every usage — never rely on defaults.

## Detect

```bash
grep -rn '@Aggregate\|@AggregateRoot' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Path A — Spring Boot (`configuration=spring`)

**Remove:**
```java
import org.axonframework.spring.stereotype.Aggregate;

@Aggregate
public class Order { … }
```

**Replace with:**
```java
import org.axonframework.extension.spring.stereotype.EventSourced;

@EventSourced(tagKey = "Order", idType = OrderId.class)
public class Order { … }
```

⚠️ Import **must** be `org.axonframework.extension.spring.stereotype.EventSourced` — the `.extension.spring.` infix
is mandatory. `org.axonframework.spring.stereotype.EventSourced` does not exist and causes a compile error.

## Path B — Native Configurer (`configuration=native`)

**Remove:**
```java
import org.axonframework.modelling.command.AggregateRoot;   // or Aggregate

@AggregateRoot   // or @Aggregate
public class Order { … }
```

**Replace with:**
```java
import org.axonframework.eventsourcing.annotation.EventSourcedEntity;

@EventSourcedEntity(tagKey = "Order", idType = OrderId.class)
public class Order { … }
```

Import: `org.axonframework.eventsourcing.annotation.EventSourcedEntity`

Path B also requires a Configurer registration — see `aggregate/RECIPE.md` § Path B for the
`EventSourcedEntityModule.autodetected(…)` call. That registration step is **component-specific** and is not part
of this atom.

## Attributes (required on both paths — never omit)

| Attribute | Value | Note |
|-----------|-------|------|
| `tagKey`  | Entity type name, e.g. `"Order"` | Always emit literally. Default equals simple class name, but renaming the class silently breaks tag routing. |
| `idType`  | Class of the AF4 `@AggregateIdentifier` field | Always emit. Default is `String.class`; mismatched type causes silent identifier-resolution failure. |

## Polymorphic aggregates

For abstract base + concrete subtypes, `concreteTypes` goes on the **abstract base only**:

```java
@EventSourced(tagKey = "Order", idType = OrderId.class, concreteTypes = { StandardOrder.class, ExpressOrder.class })
public abstract class Order { … }
```

Concrete subtypes carry **no** class-level `@EventSourced` / `@EventSourcedEntity` — they are discovered through
the base. See `aggregate/RECIPE.md` § Step P for the full polymorphic recipe.

## Gotchas

- **`.extension.spring.` in Path A** — LLMs almost always guess the wrong package. Verify with grep after editing.
- **`tagKey` defaults silently** — always write it; renames silently break event routing.
- **`idType` defaults to `String.class`** — always write it; wrong type → silent identifier failure.
- **`snapshotTriggerDefinition` on `@Aggregate`** — has no AF5 equivalent → fires Blocker B1. Do not attempt
  auto-migration; halt and let the caller resolve.
- **OpenRewrite Phase 1** sometimes rewrites `@Aggregate` → `@EventSourced` but without `tagKey`/`idType`.
  Grep for bare `@EventSourced` (no attributes) after Phase 1 and add the missing attributes.

## Used By

- **[[aggregate]]** — Step 1 (always; Path A if `configuration=spring`, Path B if `configuration=native`)
