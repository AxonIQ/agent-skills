# `@CreationPolicy` decision matrix

AF5 removes `@CreationPolicy` / `AggregateCreationPolicy`. The AF4 enum value is
expressed in AF5 by the **shape of the command handler** (static vs instance) and
the optional `@InjectEntity` parameter.

> **No compile-time signal.** Picking the wrong shape compiles cleanly and only
> surfaces at test time, typically as
> `EntityAlreadyExistsForCreationalCommandHandlerException` or as a domain rule
> being applied to an empty entity. **Always run the corresponding tests after
> migrating a handler that had `@CreationPolicy`.**

## What OpenRewrite (Migration Phase #1) already did

Before this matrix is consulted, the bulk recipe has typically:

- Removed `@CreationPolicy` and `AggregateCreationPolicy` annotations + imports.
- Added a no-arg `@EntityCreator` constructor on the entity.
- Swapped `@Aggregate` → `@EventSourced(tagKey, idType)` (Path A) or `@AggregateRoot` → `@EventSourcedEntity(...)` (Path B).

**Net effect on `CREATE_IF_MISSING`: behavior preserved.** AF5 materializes an empty
entity via the no-arg `@EntityCreator`, then runs the original instance
`@CommandHandler` — same create-or-update semantics as AF4. The per-aggregate
recipe **verifies** this; it does not "restore" anything. Restoration work is
needed only for `ALWAYS` (handler must become `static`) and edge cases below.

> ⚠️ One real semantic change worth knowing: instance handlers that AF4 would
> have rejected with `AggregateNotFoundException` now run on an empty entity in
> AF5. Domain validation (e.g. "cannot remove from empty stack") fires instead.
> Outcome — command rejected — is the same; the exception type differs. Update
> tests that pinned on `AggregateNotFoundException`.
>
> The AF5 import `org.axonframework.modelling.entity.AggregateNotFoundException`
> still resolves — the type was kept for static / creational handlers (it is
> thrown when `@InjectEntity` is non-`@Nullable` and the entity does not exist).
> So the test's compile error is "wrong assertion type", not "missing import".
> Replace with the actual project-specific domain exception. **Which exception
> depends on the project** — the recipe cannot guess. See [NPE on null state](#npe-on-null-state-gotcha)
> below for the procedure.

## Decision table

| AF4 | AF5 handler shape | `@EntityCreator` needed? | What the framework does | Failure when wrong |
|---|---|---|---|---|
| `@CreationPolicy(ALWAYS)` (creation-only command) | **`static`** `@CommandHandler` method | No (creational handler does not need the entity) | Calls handler only when no entity exists; throws `EntityAlreadyExistsForCreationalCommandHandlerException` if it does | If you used instance + no-arg `@EntityCreator`, an existing entity is overwritten silently |
| `@CreationPolicy(CREATE_IF_MISSING)` | **instance** `@CommandHandler` (NOT static) | Yes, no-arg `@EntityCreator` | Materializes an empty entity on first invocation; same handler runs whether the entity is new or pre-existing — matches AF4's create-or-update | If you make it `static + @InjectEntity`, framework treats it as creational-only and throws on existing entities |
| `@CreationPolicy(NEVER)` (or no `@CreationPolicy`) | **instance** `@CommandHandler` | No (default) | Default behavior — handler runs against existing entity | None (this is the default) |

## Recommended migration steps

1. Identify the AF4 `@CreationPolicy` annotation on each `@CommandHandler` and remove it (along with the `@CreationPolicy` and `AggregateCreationPolicy` imports).
2. Apply the row from the table above:
   - `ALWAYS` → make the method `static`. Add `EventAppender eventAppender` parameter. The first event the handler appends must carry an `@EventTag` matching the entity's `tagKey`.
   - `CREATE_IF_MISSING` → keep instance, but ensure the entity has a no-arg `@EntityCreator`. The same handler covers both the creation and update flows.
   - `NEVER` → leave as instance method (just remove the annotation).
3. Re-run the test class. Watch specifically for:
   - `EntityAlreadyExistsForCreationalCommandHandlerException` (`org.axonframework.modelling.entity`) — wrong static-vs-instance choice.
   - `NullPointerException` from a `@CommandHandler` that touches a field set only by an `@EventSourcingHandler` — see "NPE on null state" below.

## Doc-aligned alternative for `CREATE_IF_MISSING`

The official docs describe an alternative implementation using a static handler with
`@InjectEntity @Nullable`:

```java
@CommandHandler
public static void handle(IssueGiftCard cmd,
                          EventAppender eventAppender,
                          @InjectEntity @Nullable GiftCard giftCard) {
    if (giftCard != null) {
        throw new IllegalStateException("GiftCard already exists");
    }
    eventAppender.append(new GiftCardIssued(cmd.cardId(), cmd.amount()));
}
```

This makes "create only if missing" explicit. Use this **only when AF4 already
threw on existing entities** — it changes semantics for create-or-update flows.
For an architecture-neutral migration, prefer the instance-handler + no-arg
`@EntityCreator` row from the table above.

## NPE on null state (gotcha)

When migrating `CREATE_IF_MISSING`, AF5 always materializes an empty entity, so
the instance handler now runs on `this` with all fields default-initialised
(`null`, `0`, `false`). If the AF4 handler had implicit guarding via
`AggregateNotFoundException`, the AF5 handler will instead enter the body and
NPE on the first method call on a null field.

### Step-by-step fix (apply per affected handler)

1. **Read the failing test** — what condition was AF4 implicitly enforcing?
   ("Cannot remove from a non-existent army"; "Cannot finish a day before any
   day is started"; "Cannot withdraw from an empty pool".) That sentence is the
   precondition.
2. **Find the project's existing exception type for that precondition.**
   Look at sibling handlers in the same slice — they typically already
   throw a domain-specific exception when an analogous precondition fails.
   Reuse the same exception type (and message style). Don't introduce a new
   exception class just for the migration. The exact type is project-specific
   — could be a checked exception, a `RuntimeException` subclass, or an
   exception emitted by a project-specific rule / specification helper. The
   recipe does not prescribe the shape.
3. **Add an explicit guard at the top of the handler**, before any field
   access that would NPE on null state. Generic shape:
   ```java
   @CommandHandler
   void decide(SomeCommand command, EventAppender eventAppender) {
       if (this.someField == null) {
           throw new <ProjectDomainException>("<message describing the precondition>");
       }
       // … original handler body unchanged …
   }
   ```
   If the project encapsulates preconditions in a helper (rule object,
   specification, predicate, …), use *that* helper rather than the inline
   `if`. Match the project's existing style — the recipe is preserving
   architecture, not introducing one.
4. **Update the failing test's `.exception(...)` assertion** to expect the
   project's domain exception type and the message string the guard emits.
   See [test-fixture-mapping.md](test-fixture-mapping.md) for the
   `.exception(...)` assertion mechanics.
5. **Run the scoped test** to confirm the guard fires before any field access.
   If the test still fails on a different NPE, the guard was on the wrong
   field — go back to step 2, looking at the *next* field accessed in the
   handler body, and add (or extend) the guard accordingly.

### When the project has no precedent

If the project has no domain exception that captures this precondition, two
acceptable fallbacks (in priority order):

1. **Introduce one in the project's existing style** — same package, same
   naming convention, same supertype as other domain exceptions in that
   slice. This raises the migration commit beyond pure preservation but
   keeps the AF5 behaviour explicit and greppable.
2. **Inline `Exception.class` test expectation + TODO** — `expect Exception.class`
   in the test and add a `// TODO: harden domain model — handler should reject
   empty <Entity> with a domain exception`. Use only when introducing the
   exception would meaningfully expand the migration commit's scope.

### What NOT to do

- Don't keep `AggregateNotFoundException` in test assertions hoping AF5 throws
  it for instance handlers. It does not.
- Don't invent a generic `EntityNotFoundException` if the project does not use
  one. Match the project's existing exception vocabulary.
- Don't drop a bare `if (...) throw new IllegalStateException(...)` if the
  project has a richer domain-exception pattern — use the project's pattern.
