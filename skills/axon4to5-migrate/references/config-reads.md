# Recipe: config-reads (class reads AF4 `Configuration` to look up buses / processors)

Atomic migration of ONE class that injects AF4 `Configuration` / `EventProcessingConfiguration` to look up `commandBus()` / `queryBus()` / `queryUpdateEmitter()` / event-processor components instead of using the high-level gateway.

Rare except for ops endpoints (reset, replay, DLQ inspection). When the candidate uses the high-level gateway directly, route to the matching gateway recipe instead.

## Inputs

- `target` — FQ class (required)
- `target-bus` — `command` | `query` | `event-processor` (required; picks the rewrite block)
- `wiring` — `spring-boot` | `framework-config` (from pinned decisions)

## Preflight

1. Compile clean? If yes → `AskUserQuestion` Skip / Deep verify.
2. No need to consult [blockers.md](blockers.md) — this recipe has no AF5 gaps.

## Procedure

### Step 1 — Switch injected bean type

| AF4 field type | AF5 replacement |
|---|---|
| `org.axonframework.config.Configuration` | `org.axonframework.common.configuration.Configuration` (read-only) — when class only reads. |
| `org.axonframework.config.EventProcessingConfiguration` | `org.axonframework.common.configuration.AxonConfiguration` — entry point for module lookups. |
| `org.axonframework.config.Configuration` (touches root lifecycle) | `org.axonframework.common.configuration.AxonConfiguration`. |

Rename field + constructor param (`eventProcessingConfiguration` → `axonConfiguration`, etc.).

- **Path A (Spring Boot):** `AxonConfiguration` / `Configuration` are auto-beans; constructor injection unchanged.
- **Path B (framework Configurer):** pass `AxonConfiguration` from `configurer.start()`.

### Step 2 — Rewrite lookups per `target-bus`

#### `target-bus: command`

| AF4 | AF5 |
|---|---|
| `config.commandBus()` | `axonConfig.getOptionalComponent(CommandBus.class).orElseThrow()` |
| `config.findComponent(CommandBus.class)` | `axonConfig.getOptionalComponent(CommandBus.class)` |

FQNs: `org.axonframework.commandhandling.CommandBus` (AF4) → `org.axonframework.messaging.commandhandling.CommandBus` (AF5).

#### `target-bus: query`

| AF4 | AF5 |
|---|---|
| `config.queryBus()` | `axonConfig.getOptionalComponent(QueryBus.class).orElseThrow()` |
| `config.queryUpdateEmitter()` | `axonConfig.getOptionalComponent(QueryUpdateEmitter.class).orElseThrow()` |
| `config.findComponent(QueryBus.class)` | `axonConfig.getOptionalComponent(QueryBus.class)` |

FQNs: `org.axonframework.queryhandling.{QueryBus, QueryUpdateEmitter}` (AF4) → `org.axonframework.messaging.queryhandling.{QueryBus, QueryUpdateEmitter}` (AF5).

> If `QueryUpdateEmitter` lookup happens inside a `@QueryHandler` method, prefer the AF5 method-parameter form (handled by the `query-handler` recipe).

#### `target-bus: event-processor`

Event-processor components live inside **per-processor modules** named `"EventProcessor[<processorName>]"` (one module per processor, NOT a single `"EventProcessing"` module). Use the two-step lookup:

| AF4 call | AF5 replacement |
|---|---|
| `epc.eventProcessor(name)` | `axonConfig.getModuleConfiguration("EventProcessor[" + name + "]").flatMap(m -> m.getOptionalComponent(EventProcessor.class))` |
| `epc.eventProcessor(name, EventProcessor.class)` | same with the specific type |
| `epc.eventProcessorByProcessingGroup(group)` | `getModuleConfiguration("EventProcessor[" + group + "]")…getOptionalComponent(EventProcessor.class)` |
| `epc.eventProcessorByProcessingGroup(group, StreamingEventProcessor.class)` | same with `StreamingEventProcessor.class` |
| `epc.tokenStore(processor)` | `getModuleConfiguration("EventProcessor[" + processor + "]")…getOptionalComponent(TokenStore.class)` |
| `epc.sequencedDeadLetterProcessor(group)` | `getModuleConfiguration("EventProcessor[" + group + "]")…getOptionalComponent(SequencedDeadLetterProcessor.class, "EventHandlingComponent[" + group + "][" + componentName + "]")` |

`SequencedDeadLetterProcessor` named-component lookup: the processor module typically holds many (one per handling component). Disambiguate with `"EventHandlingComponent[<processorName>][<componentName>]"`.

**Component type moves:**
- `TrackingEventProcessor` → `StreamingEventProcessor` (`TrackingEventProcessor` removed in AF5).
- All processor types moved under `org.axonframework.messaging.eventhandling.processing.*`.
- AF4 specifically typed `TrackingEventProcessor.class` → broaden to `StreamingEventProcessor` (gets `supportsReset()`, `resetTokens()`, `start()`, `shutdown()` without committing to `PooledStreamingEventProcessor`).

**Async lifecycle.** AF4 sync → AF5 async. Return type `void` → `CompletableFuture<Void>`:
- `processor.start()`, `shutdown()` (renamed from AF4 `shutDown()` — capital `D` → lowercase), `resetTokens()`, DLQ `processAny()`, DLQ `process(...)`.

Bridge with `.orTimeout(<d>, <u>).join()` (never naked `.join()` / `.get()`):
```java
eventProcessor.shutdown().orTimeout(30, TimeUnit.SECONDS).join();
eventProcessor.resetTokens().orTimeout(30, TimeUnit.SECONDS).join();
eventProcessor.start().orTimeout(30, TimeUnit.SECONDS).join();
```

If existing code has naked `.join()`, **upgrade** to `.orTimeout(...).join()` (default 30s).

> **DLQ flag.** Read-side lookup compiles against free AF5. The underlying DLQ **store / wiring** (JPA dead-letter sequence, persistent DLQ beans) is Axoniq commercial. If the class also configures a DLQ impl, flag as commercial — belongs to a `axon4-to-axoniq5-*` recipe.

### Step 3 — Sweep imports

| target-bus | Remove (AF4) | Add (AF5) |
|---|---|---|
| `command` | `org.axonframework.config.Configuration`, `org.axonframework.commandhandling.CommandBus` | `org.axonframework.common.configuration.{Configuration, AxonConfiguration}`, `org.axonframework.messaging.commandhandling.CommandBus` |
| `query` | `org.axonframework.config.Configuration`, `org.axonframework.queryhandling.{QueryBus, QueryUpdateEmitter}` | `org.axonframework.common.configuration.{Configuration, AxonConfiguration}`, `org.axonframework.messaging.queryhandling.{QueryBus, QueryUpdateEmitter}` |
| `event-processor` | `org.axonframework.config.*`, AF4-located `TrackingEventProcessor`, `EventProcessor`, `StreamingEventProcessor`, `TokenStore` | `org.axonframework.common.configuration.AxonConfiguration`, `org.axonframework.messaging.eventhandling.processing.{EventProcessor, streaming.StreamingEventProcessor, streaming.pooled.PooledStreamingEventProcessor, subscribing.SubscribingEventProcessor}`, `org.axonframework.messaging.eventhandling.deadletter.SequencedDeadLetterProcessor`, AF5-located `TokenStore` |

AF4 commonly injects **both** `EventProcessingConfiguration` and `TokenStore` (the latter for `fetchSegments` / `fetchToken`). AF5 routes both through `axonConfiguration.getOptionalComponent(TokenStore.class[, name])` — the separately injected `TokenStore` field is usually now redundant. Delete it (and its constructor param).

## End condition

Compile-only via `axon4to5-isolatedtest`:
```
target-name: <ClassSimpleName>
main-sources: [<Class>.java]
test-sources: [<Class>Test.java]    # [] if no tests
extra-deps: [axon-messaging, axon-configuration]
```

## Output

```yaml
result: success | skipped | rejected | needs-decision | failed
target: <FQ class>
reason: <one short line>
decisions:
  path: A (Spring Boot) | B (framework Configurer)
  target-bus: command | query | event-processor
  dlq-sites-flagged: [<file:line>, …] | none      # event-processor only
```

## Reference pair (AF4 → AF5)

Bundled in [evals/fixtures/](../evals/fixtures/):

- **Spring `@Component` reading `EventProcessingConfiguration` for `eventProcessorByProcessingGroup` + `tokenStore`:** `axon4/heroes/StreamProcessorsOperations.java` ↔ `axon5/heroes/StreamProcessorsOperations.java`. The AF5 file shows the two-step `getModuleConfiguration(...)` lookup AND the async `.orTimeout(...).join()` bridge for `start()` / `shutdown()` / `resetTokens()`.
