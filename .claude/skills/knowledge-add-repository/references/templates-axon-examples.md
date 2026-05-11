# Template — `axon-examples` per-repo detail file

Use this template when `repo_type: axon-examples`. There is **one file per
variant** (one for the axon4 side, one for the axon5 side, and one per
additional axon5 migration strategy). Pairing is expressed through frontmatter
cross-links — `migrated_from` (scalar, on the target) and `migrated_to` (list,
on the source).

Detail files live at:

```
.knowledge/repositories/axon-examples/axon-examples_<variant>_<app>.md
```

The filename mirrors the submodule path, joining components with `_`. For an
alternative migration target, append a suffix:
`axon-examples_axon5_<app>_<strategy>.md`.

## Filled-in example — axon4 side

```markdown
---
repo_type: axon-examples
repo_name: orderservice (axon4)
submodule_path: .knowledge/repositories/axon-examples/axon4/orderservice
url: https://github.com/AxonIQ/giftcard-demo.git
branch: main
variant: axon4
language: Kotlin
build_tool: gradle
architecture: Vertical Slice
keywords:
  - orders
  - cqrs
  - event sourcing
  - vertical slice
migrated_to:
  - axon-examples_axon5_orderservice.md
  - axon-examples_axon5_orderservice_alt.md
---

# orderservice — axon4

## Description

Source state of the order-service example as it ships with Axon 4. Demonstrates
the classic aggregate-root pattern and saga-based process management.

## Patterns / focus areas

- Aggregate roots with `@AggregateIdentifier` and `@EventSourcingHandler`.
- `PaymentSaga` orchestrating order → payment → shipping with `@SagaEventHandler`.
- `@CommandHandler` returning `void`; client code blocks on the command bus.
- Spring Boot 2.x autoconfiguration.

## Highlights

- Start with `OrderAggregate.kt` — it's the most readable entry point into the
  command/event model.
- Build & run: `./gradlew bootRun` (Gradle wrapper checked in).
- Look at `PaymentSaga.kt` to compare against the axon5 repository-based
  rewrite — the saga lifecycle is where the migration is most visible.
```

## Filled-in example — axon5 target side

```markdown
---
repo_type: axon-examples
repo_name: orderservice (axon5)
submodule_path: .knowledge/repositories/axon-examples/axon5/orderservice
url: https://github.com/AxonIQ/giftcard-demo.git
branch: feat/axon5
commit: 1a2b3c4
variant: axon5
language: Kotlin
build_tool: gradle
architecture: Vertical Slice
keywords:
  - orders
  - cqrs
  - dcb
  - reactive handlers
migrated_from: axon-examples_axon4_orderservice.md
---

# orderservice — axon5

## Description

orderservice migrated to Axon 5. Same business behavior as the axon4 source;
the differences ARE the migration.

## Patterns / focus areas

- **DCB instead of aggregate roots** — `OrderState` is reconstituted via the
  new state-based modelling API.
- **Reactive handlers** — command handlers return `CompletableFuture<Result>`.
- **AxonTestFixture** — Spring Boot integration tests via a custom
  `@OrderserviceAxonSpringBootTest` annotation.

## Migration notes

- **PaymentSaga** was migrated using a **repository-based state management
  pattern** instead of the (not-yet-released) Workflow extension. Treat this
  as the recommended pattern when migration skills encounter sagas.
- **Deadlines** were not migrated — without the Workflow extension there is
  no standard way to implement timeouts in Axon 5. Flag this if a migration
  target uses `@DeadlineHandler`.
- The previous `void`-returning command handlers now return
  `CompletableFuture<Result>`; callers no longer block on the gateway.
- Spring Boot autoconfig moved packages — `axon-spring-boot-autoconfigure`
  reorganized; check imports in `OrderserviceAxonAutoConfiguration.kt`.

## Highlights

- Build & run: `./gradlew bootRun`. The integration tests
  (`./gradlew test`) demonstrate the AxonTestFixture pattern most clearly.
- The diff against `axon-examples_axon4_orderservice.md` is the migration
  artifact — see the Migration Diff callout in `axon-examples/INDEX.md`.
- Avoid copying the legacy `@SagaEventHandler` annotations from the axon4
  side — they're gone in Axon 5 and the repository-state pattern replaces them.
```

## Empty scaffold — axon4 source

```markdown
---
repo_type: axon-examples
repo_name: <app> (axon4)
submodule_path: .knowledge/repositories/axon-examples/axon4/<app>
url: <git URL>
branch: <branch or omit>
commit: <short-hash or omit>
variant: axon4
language: Kotlin | Java
build_tool: maven | gradle
architecture: <Vertical Slice | Hexagonal | CRUD | …>
keywords:
  - <term>
  - <term>
migrated_to:
  - <axon-examples_axon5_<app>.md>
---

# <app> — axon4

## Description

<What this app demonstrates in Axon 4.>

## Patterns / focus areas

- <pattern 1>
- <pattern 2>

## Highlights

- <How to build/run, where to start reading, anything subtle.>
```

## Empty scaffold — axon5 target

```markdown
---
repo_type: axon-examples
repo_name: <app> (axon5)
submodule_path: .knowledge/repositories/axon-examples/axon5/<app>
url: <git URL>
branch: <branch or omit>
commit: <short-hash or omit>
variant: axon5
language: Kotlin | Java
build_tool: maven | gradle
architecture: <…>
keywords:
  - <term>
  - <term>
migrated_from: <axon-examples_axon4_<app>.md>
---

# <app> — axon5

## Description

<What this migrated app demonstrates.>

## Patterns / focus areas

- <focus 1>
- <focus 2>

## Migration notes

- <Inline migration choice / alternative considered / limitation.>
- <Another note — the kind of thing a migration skill should learn from.>

## Highlights

- <Where to start reading, build/run commands, files to jump to.>
```

## Field rules

- `variant`, `language`, and `build_tool` are **required**. The skill must ask
  the user for them if missing — they're surfaced in `INDEX.md` so readers can
  pick the right variant without opening detail files.
- `migrated_from` is **always scalar**: a migration has exactly one source.
- `migrated_to` is **a list**: one source can be migrated multiple times with
  different strategies. Use scalar form only if there's exactly one target
  today; promote to a list as soon as a second target appears.
- Cross-links must be bidirectional. If file A's `migrated_to` contains file
  B's filename, then file B's `migrated_from` must equal A's filename. The
  skill maintains this invariant when adding or pairing.
- `## Migration notes` belongs on the **axon5** (target) side only. It captures
  decisions made during the migration, not properties of the axon4 source.
- `## Highlights` is mandatory as a section heading on both sides.

## When only one side exists

If the counterpart hasn't been migrated yet:

- On the axon4 side, leave `migrated_to:` absent (or as an empty list) and add
  a `**Status:**` line in the body like
  `**Status:** Awaiting Axon 5 migration.`
- On the axon5 side, populate `migrated_from:` only if there's a real source
  file in this repo; otherwise omit and add a `**Status:**` line noting that
  the source lives upstream.

The INDEX entry should also reflect this (see `index-entry-templates.md`).
