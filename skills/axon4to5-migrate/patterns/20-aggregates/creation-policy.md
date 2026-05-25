# @CreationPolicy Removal

AF4's `@CreationPolicy(AggregateCreationPolicy.*)` annotation is removed in AF5. The creation semantics are
replaced by the `@EntityCreator` constructor and the presence/absence of static vs instance `@CommandHandler`.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.modelling.command.CreationPolicy` | *(remove)* |
| `org.axonframework.modelling.command.AggregateCreationPolicy` | *(remove)* |

## Detection

**Pre-migration (AF4 original):**

```bash
grep -rn '@CreationPolicy\|AggregateCreationPolicy\|import.*CreationPolicy' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
# Stray references OR could not strip (rare) and entity files that still need
# a manual ALWAYS-handler flip to `static` — list all @CommandHandler-bearing
# files inside @EventSourced classes for review.
grep -rln '@CommandHandler' --include='*.java' --include='*.kt' --include='*.scala' . \
  | xargs grep -l '@EventSourced\|@EventSourcedEntity'
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

## Migration by policy value

### ALWAYS — creation handler

```java
// AF4
@CommandHandler
@CreationPolicy(AggregateCreationPolicy.ALWAYS)
public static MyAggregate create(CreateCommand cmd) { ... }

// AF5 — make the handler static (ALWAYS = factory pattern)
@CommandHandler
public static MyAggregate create(CreateCommand cmd, EventAppender eventAppender) {
    eventAppender.append(new CreatedEvent(cmd.id()));
    return new MyAggregate();
}
```

### CREATE_IF_MISSING — upsert handler

```java
// AF4
@CommandHandler
@CreationPolicy(AggregateCreationPolicy.CREATE_IF_MISSING)
public void handle(UpsertCommand cmd) { ... }

// AF5 — instance handler; @EntityCreator on no-arg constructor handles the "create" case
// No @CreationPolicy annotation needed
@CommandHandler
public void handle(UpsertCommand cmd, EventAppender eventAppender) {
    eventAppender.append(new UpsertedEvent(cmd.id()));
}
```

### NEVER (default) — normal instance handler

```java
// AF4 (explicit or absent)
@CommandHandler
@CreationPolicy(AggregateCreationPolicy.NEVER)
public void handle(UpdateCommand cmd) { ... }

// AF5 — just remove the annotation; instance @CommandHandler is the default
@CommandHandler
public void handle(UpdateCommand cmd, EventAppender eventAppender) {
    eventAppender.append(new UpdatedEvent(cmd.id()));
}
```

## Notes

- **Remove the annotation and both imports** — no replacement annotation is needed.
- **ALWAYS → static factory** is the most common case where OpenRewrite does NOT flip to `static` — always
  verify the handler is static after removing `@CreationPolicy(ALWAYS)`.
- **`@EntityCreator` on the no-arg constructor** is required in all cases — see [entity-creator.md](entity-creator.md).
- **OpenRewrite status:** Partial — `RemoveAnnotation` strips `@CreationPolicy` and `ConvertCommandHandlerConstructorToStaticMethod` converts AF4 command-handler constructors to AF5 static factory methods; AI still flips ALWAYS handlers that weren't constructors to `static` and reviews CREATE_IF_MISSING semantics manually.
