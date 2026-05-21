# @CreationPolicy Removal

AF4's `@CreationPolicy(AggregateCreationPolicy.*)` annotation is removed in AF5. The creation semantics are
replaced by the `@EntityCreator` constructor and the presence/absence of static vs instance `@CommandHandler`.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.modelling.command.CreationPolicy` | *(remove)* |
| `org.axonframework.modelling.command.AggregateCreationPolicy` | *(remove)* |

## Detection

```bash
grep -rn '@CreationPolicy\|AggregateCreationPolicy\|import.*CreationPolicy' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

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
