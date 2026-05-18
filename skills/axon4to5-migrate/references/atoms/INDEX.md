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
| [[aggregate-annotation]] | `@Aggregate`/`@AggregateRoot` → `@EventSourced`/`@EventSourcedEntity`; `tagKey`/`idType` attributes | aggregate |
| [[entity-creator]] | `@EntityCreator` on the no-arg constructor; `.reflection.` import infix | aggregate |
| [[aggregate-lifecycle]] | `AggregateLifecycle.apply(…)` → `EventAppender.append(…)`; `.messaging.` import infix | aggregate |
| [[aggregate-member]] | `@AggregateMember` → `@EntityMember`; Map-typed Blocker B2; child entity requirements | aggregate |

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
| [[processing-group-annotation]] | `@ProcessingGroup` → `@Namespace`; binding contract; external reference grep | event-processor, query-handler |
| [[metadata-value]] | `@MetaDataValue` (AF4) → `@MetadataValue` (AF5) — casing + package | event-processor, query-handler |
| [[message-accessors]] | `getPayload()` → `payload()`, `getMetaData()` → `metaData()`, etc. | event-processor, saga, interceptors |
| [[command-gateway]] | `CommandGateway` field → `CommandDispatcher` method param; async dispatch | event-processor, saga |
| [[sequencing-policy]] | YAML/`@Bean` → `@SequencingPolicy` class annotation; `SequencingPolicy` interface rewrite | event-processor |

### Query Handling

| Atom | What it covers | Components |
|------|----------------|-----------|
| [[query-handler-annotation]] | `@QueryHandler` import move: `queryhandling` → `messaging.queryhandling.annotation` | query-handler |
| [[query-payload-record]] | `@QueryHandler(queryName)` removal; introduce `@Query`-annotated top-level payload record | query-handler |
| [[query-update-emitter]] | `QueryUpdateEmitter` constructor field → method param; `emit()` 2-arg → 3-arg | query-handler |

### Interceptors

| Atom | What it covers | Components |
|------|----------------|-----------|
| [[interceptor-dispatch]] | `handle(List<M>)` → `interceptOnDispatch(M, @Nullable ProcessingContext, Chain)`; BiFunction collapse | interceptors |
| [[interceptor-handler]] | `handle(UnitOfWork, InterceptorChain)` → `interceptOnHandle(M, ProcessingContext, Chain)`; `chain.proceed(message, context)` | interceptors |

### Saga

| Atom | What it covers | Components |
|------|----------------|-----------|
| [[saga-spi-to-spring-component]] | `@Saga` → `@Component @DisallowReplay`; both AF4 import paths | saga |
| [[saga-event-handler]] | `@SagaEventHandler`/`@StartSaga`/`@EndSaga` → `@EventHandler` + JPA state lookup; `SagaLifecycle` removal | saga |

### Infrastructure

| Atom | What it covers | Components |
|------|----------------|-----------|
| [[unit-of-work]] | `UnitOfWork` → `ProcessingContext`; `InterceptorChain.proceedSync(context)`; lifecycle hooks | interceptors, saga, event-processor |

### Testing

| Atom | What it covers | Components |
|------|----------------|-----------|
| [[aggregate-test-fixture]] | `AggregateTestFixture` → `AxonTestFixture`; DSL changes; AF5 exception flip | aggregate |

## Cross-reference: component → atoms

| Component recipe | Atoms applied |
|---|---|
| `aggregate` | aggregate-annotation · entity-creator · aggregate-lifecycle · event-sourcing-handler · command-handler · command-annotation · event-annotation · aggregate-member (M) · aggregate-test-fixture (T) |
| `event-processor` | processing-group-annotation · event-handler · metadata-value · message-accessors · command-gateway (4) · sequencing-policy (6/7) · unit-of-work (when UnitOfWork used) |
| `interceptors` | interceptor-dispatch (dispatch) · interceptor-handler (handler) · unit-of-work (when UnitOfWork lifecycle hooks used) · message-accessors (when body uses message API) |
| `query-handler` | query-handler-annotation · query-payload-record (queryName) · query-update-emitter (QUE) · processing-group-annotation (ProcessingGroup) · metadata-value (MetaDataValue) · event-handler (QUE-touched methods) |
| `saga` | saga-spi-to-spring-component · saga-event-handler · command-gateway (when CommandGateway present) · message-accessors (when body uses message API) |
| `command-gateway` | — (no atoms) |
| `event-store` | — (no atoms) |
| `query-gateway` | — (no atoms) |

## Adding a new atom

1. Create `references/atoms/<name>.md` using the YAML frontmatter + sections format of any existing atom.
2. Add a row to this INDEX under the correct category.
3. Add the atom to the `used-by:` field in the relevant component RECIPE.md's `## References / Atoms` section.
4. Add a `## Used By` entry in the new atom pointing back to the component.
