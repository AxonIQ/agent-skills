# Atom Index — Axon Framework 4 → 5 Migration

Atoms are **single-responsibility API change recipes**. Each atom covers exactly one AF4→AF5 API change: the
before/after transformation, correct imports, gotchas, and which component recipes use it.

Component recipes (aggregates, event-processors, etc.) **compose atoms** — they list which atoms apply and under
what conditions, and load them during FLOW.md S3 (Read References). The atoms are the canonical source of truth
for each API change; the component recipes provide scope, blockers, and component-specific orchestration.

## Navigation

### Entity Lifecycle (Aggregates)

| Atom | What it covers | Component |
|------|----------------|-----------|
| [[entity-annotation]] | `@Aggregate`/`@AggregateRoot` → `@EventSourced`/`@EventSourcedEntity`; `tagKey`/`idType` attributes | aggregate |
| [[entity-creator]] | `@EntityCreator` on the no-arg constructor; `.reflection.` import infix | aggregate |
| [[event-appender]] | `AggregateLifecycle.apply(…)` → `EventAppender.append(…)`; `.messaging.` import infix | aggregate |
| [[entity-member]] | `@AggregateMember` → `@EntityMember`; Map-typed Blocker B2; child entity requirements | aggregate |

### Handler Annotations

| Atom | What it covers | Components |
|------|----------------|-----------|
| [[event-sourcing-handler]] | `@EventSourcingHandler` import package move | aggregate |
| [[command-handler]] | `@CommandHandler` import package move; `EventAppender` parameter rule | aggregate |
| [[event-handler]] | `@EventHandler`, `@DisallowReplay`, `@ResetHandler` import package moves | event-processor |

### Message Classes

| Atom | What it covers | Components |
|------|----------------|-----------|
| [[command-annotation]] | `@Command` class annotation; `@TargetAggregateIdentifier` → `@TargetEntityId`; `@RoutingKey` → `@Command(routingKey=…)` | aggregate |
| [[event-annotation]] | `@Event` class annotation; `@EventTag`; `@Revision` → `@Event(version=…)` | aggregate |

### Event Processing

| Atom | What it covers | Components |
|------|----------------|-----------|
| [[namespace-annotation]] | `@ProcessingGroup` → `@Namespace`; binding contract; external reference grep | event-processor |
| [[metadata-value]] | `@MetaDataValue` (AF4) → `@MetadataValue` (AF5) — casing + package | event-processor |
| [[message-accessors]] | `getPayload()` → `payload()`, `getMetaData()` → `metaData()`, etc. | event-processor, saga, interceptors |
| [[command-dispatcher]] | `CommandGateway` field → `CommandDispatcher` method param; async dispatch | event-processor |
| [[sequencing-policy]] | YAML/`@Bean` → `@SequencingPolicy` class annotation; `SequencingPolicy` interface rewrite | event-processor |

### Infrastructure

| Atom | What it covers | Components |
|------|----------------|-----------|
| [[processing-context]] | `UnitOfWork` → `ProcessingContext`; `InterceptorChain.proceedSync(context)` | interceptors, saga, event-processor |

### Testing

| Atom | What it covers | Components |
|------|----------------|-----------|
| [[test-fixture]] | `AggregateTestFixture` → `AxonTestFixture`; DSL changes; AF5 exception flip | aggregate |

## Cross-reference: component → atoms

| Component recipe | Atoms applied |
|---|---|
| `aggregate` | entity-annotation · entity-creator · event-appender · event-sourcing-handler · command-handler · command-annotation · event-annotation · entity-member (M) · test-fixture (T) |
| `event-processor` | namespace-annotation · event-handler · metadata-value · message-accessors · command-dispatcher (4) · sequencing-policy (6/7) · processing-context (when UnitOfWork used) |
| `interceptors` | processing-context |
| `saga` | processing-context · message-accessors |

## Adding a new atom

1. Create `references/atoms/<name>.md` using the YAML frontmatter + sections format of any existing atom.
2. Add a row to this INDEX under the correct category.
3. Add the atom to the `used-by:` field in the relevant component RECIPE.md's `## References / Atoms` section.
4. Add a `## Used By` entry in the new atom pointing back to the component.
