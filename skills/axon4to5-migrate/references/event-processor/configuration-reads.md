# Event-processor configuration reads

Atomic migration of ONE class that **reads** AF4 `EventProcessingConfiguration` / `Configuration` to look up an event processor, token store, or dead-letter processor and call methods on it. Typically a Spring `@Component` ops endpoint (reset, replay, DLQ inspection) that runs lifecycle on the looked-up processor.

Used by the main `event-processor` recipe when a candidate class is **read-side** (injects the configuration to look up event-processor components) rather than the `@EventHandler`-bearing class itself.

## Canonical reference

- [../../docs/paths/configuration.adoc](../../docs/paths/configuration.adoc) — `AxonConfiguration`, `getModuleConfiguration("EventProcessor[...]")`, two-step lookup.
- [../../docs/paths/projectors-event-processors.adoc](../../docs/paths/projectors-event-processors.adoc) — `StreamingEventProcessor`, async lifecycle.
- [../../docs/paths/index.adoc](../../docs/paths/index.adoc) §"Import and package changes" — `org.axonframework.config` → `org.axonframework.common.configuration`.

## Goal

- Injected bean changed from AF4 `EventProcessingConfiguration` / `Configuration` to AF5 `AxonConfiguration` (or `Configuration` when only reading, never starting/stopping the root).
- AF4 dedicated lookups (`eventProcessor`, `eventProcessorByProcessingGroup`, `sequencedDeadLetterProcessor`, `tokenStore`) rewritten to the AF5 generic two-step lookup against the per-processor module.
- Looked-up component type updated where AF5 renamed/moved it (`TrackingEventProcessor` → `StreamingEventProcessor`; package moves to `org.axonframework.messaging.eventhandling.processing.*`).
- Lifecycle / DLQ calls adapted to async — `start()`, `shutdown()`, `resetTokens()`, `processAny()`, `process(...)` now return `CompletableFuture<Void>`. `shutDown()` (AF4, capital `D`) renamed to `shutdown()` (AF5).

## FQN cheat sheet

### AF4 (remove)

| Element | FQN |
|---|---|
| `Configuration` | `org.axonframework.config.Configuration` |
| `EventProcessingConfiguration` | `org.axonframework.config.EventProcessingConfiguration` |
| `TrackingEventProcessor` | `org.axonframework.eventhandling.TrackingEventProcessor` |
| `EventProcessor` | `org.axonframework.eventhandling.EventProcessor` |
| `StreamingEventProcessor` (AF4 loc.) | `org.axonframework.eventhandling.StreamingEventProcessor` |
| `SequencedDeadLetterProcessor` | `org.axonframework.eventhandling.deadletter.SequencedDeadLetterProcessor` |
| `TokenStore` | `org.axonframework.eventhandling.tokenstore.TokenStore` |

### AF5 (add)

| Element | FQN |
|---|---|
| `AxonConfiguration` | `org.axonframework.common.configuration.AxonConfiguration` |
| `Configuration` (read-only parent) | `org.axonframework.common.configuration.Configuration` |
| `EventProcessor` | `org.axonframework.messaging.eventhandling.processing.EventProcessor` |
| `StreamingEventProcessor` | `org.axonframework.messaging.eventhandling.processing.streaming.StreamingEventProcessor` |
| `PooledStreamingEventProcessor` | `org.axonframework.messaging.eventhandling.processing.streaming.pooled.PooledStreamingEventProcessor` |
| `SubscribingEventProcessor` | `org.axonframework.messaging.eventhandling.processing.subscribing.SubscribingEventProcessor` |
| `SequencedDeadLetterProcessor` | `org.axonframework.messaging.eventhandling.deadletter.SequencedDeadLetterProcessor` |
| `TokenStore` | confirm in source — moved under `org.axonframework.eventstreaming.tokenstore.*` |

## Procedure

### 1. Locate

```bash
grep -RlnE 'org\.axonframework\.config\.(Configuration|EventProcessingConfiguration)' \
     --include='*.java' --include='*.kt' <target>/src
```

Pick a file that **uses** the AF4 type for a read operation on event-processor components (`eventProcessor`, `eventProcessorByProcessingGroup`, `tokenStore`, `sequencedDeadLetterProcessor`). Files that touch only root buses / event store belong to the [command-gateway](../command-gateway/configuration-reads.md), [query-gateway](../query-gateway/configuration-reads.md), or [event-storage-engine](../event-storage-engine/configuration.md) reads file.

### 2. Switch the injected bean type

- If class only reads (never starts/shuts down root) → `Configuration` (`org.axonframework.common.configuration.Configuration`).
- If class also touches root lifecycle (rare for readers) → `AxonConfiguration` (`org.axonframework.common.configuration.AxonConfiguration`).
- If class injected `EventProcessingConfiguration` directly → switch to `AxonConfiguration` (entry point for module lookups).
- Rename field to track new type (`eventProcessingConfiguration` → `axonConfiguration`). Update constructor parameter.

**How the configuration is obtained (path-conditional):**
- **Path A (Spring Boot):** `AxonConfiguration` is auto-created as a Spring bean by the AF5 starter — annotate the class with the existing Spring stereotype (`@Component` / `@Service`) and use constructor injection / `@Autowired` as before. `@Transactional` etc. preserved as-is.
- **Path B (framework Configurer):** the live `AxonConfiguration` returned by `EventSourcingConfigurer.create().…start()` is wired in by the bootstrap that built it — typically a constructor argument:
  ```java
  var config = configurer.start();
  var reader = new MyReader(config);                        // pass AxonConfiguration directly
  // OR pass the read-only view if the reader never touches lifecycle:
  var reader = new MyReader((Configuration) config);
  ```
  Steps 3–6 are identical in both paths.

### 3. Rewrite AF4 event-processor lookups → AF5 two-step

Event-processor components live inside **per-processor modules**: `axonConfig.getModuleConfiguration("<module-name>").flatMap(m -> m.getOptionalComponent(<Type>.class[, "<componentName>"]))`.

Module name strings are case-sensitive **conventions** emitted by AF5 `*Module` classes. The event-processor module name is `"EventProcessor[" + processorName + "]"` (one module per processor, **not** a single `"EventProcessing"` module).

| AF4 call | AF5 replacement |
|---|---|
| `epc.eventProcessor(name)` | `axonConfig.getModuleConfiguration("EventProcessor[" + name + "]").flatMap(m -> m.getOptionalComponent(EventProcessor.class))` |
| `epc.eventProcessor(name, EventProcessor.class)` | `axonConfig.getModuleConfiguration("EventProcessor[" + name + "]").flatMap(m -> m.getOptionalComponent(EventProcessor.class))` |
| `epc.eventProcessorByProcessingGroup(group)` | `axonConfig.getModuleConfiguration("EventProcessor[" + group + "]").flatMap(m -> m.getOptionalComponent(EventProcessor.class))` |
| `epc.eventProcessorByProcessingGroup(group, StreamingEventProcessor.class)` | `axonConfig.getModuleConfiguration("EventProcessor[" + group + "]").flatMap(m -> m.getOptionalComponent(StreamingEventProcessor.class))` |
| `epc.tokenStore(processor)` | `axonConfig.getModuleConfiguration("EventProcessor[" + processor + "]").flatMap(m -> m.getOptionalComponent(TokenStore.class))` |
| `epc.sequencedDeadLetterProcessor(group)` | `axonConfig.getModuleConfiguration("EventProcessor[" + group + "]").flatMap(m -> m.getOptionalComponent(SequencedDeadLetterProcessor.class, "EventHandlingComponent[" + group + "][" + componentName + "]"))` |

Module-scoped lookups in AF4 returned `Optional<T>` already — same shape after rewrite.

#### DLQ named-component lookup

`SequencedDeadLetterProcessor` lives **inside** the processor module, but the module typically holds many — one per event-handling component. Disambiguate with the AF5 component name `"EventHandlingComponent[" + processorName + "][" + componentName + "]"`:

```java
axonConfig.getModuleConfiguration("EventProcessor[" + processorName + "]")
          .flatMap(m -> m.getOptionalComponent(
              SequencedDeadLetterProcessor.class,
              "EventHandlingComponent[" + processorName + "][" + componentName + "]"))
          .ifPresent(...);
```

> **DLQ flag.** `SequencedDeadLetterProcessor` itself is in the AF5 free build (`org.axonframework.messaging.eventhandling.deadletter`). Read-side lookup compiles against free AF5. **However**, the underlying DLQ store / wiring (e.g. JPA dead-letter sequence, persistent dead-letter queue beans) is Axoniq commercial. If the candidate class also instantiates / configures a DLQ implementation, flag it as commercial — that part belongs to a `axon4-to-axoniq5-*` recipe.

### 4. Update component types

- `TrackingEventProcessor` → `StreamingEventProcessor` (and import). `TrackingEventProcessor` is **removed** in AF5.
- `EventProcessor`, `StreamingEventProcessor`, `PooledStreamingEventProcessor`, `SubscribingEventProcessor`: package moved under `org.axonframework.messaging.eventhandling.processing.*`.
- If AF4 was specifically typed (`TrackingEventProcessor.class`), broaden to `StreamingEventProcessor` — gives `supportsReset()`, `resetTokens()`, `start()`, `shutdown()` without committing to `PooledStreamingEventProcessor`.

### 5. Adapt async lifecycle / DLQ calls

AF4 sync → AF5 async. Return type changes from `void` to `CompletableFuture<Void>`:

- `processor.start()` → `CompletableFuture<Void>`
- `processor.shutDown()` (AF4) → `processor.shutdown()` (AF5) → `CompletableFuture<Void>` — **rename method** (capital `D` → lowercase `d`) and add the future handling.
- `processor.resetTokens()` → `CompletableFuture<Void>`
- DLQ `processor.processAny()` → `CompletableFuture<Void>`
- DLQ `processor.process(...)` → `CompletableFuture<Void>`

Bridge with `.orTimeout(<duration>, <unit>).join()` (project rule on `CompletableFuture` blocking — never naked `.join()` / `.get()`):

```java
eventProcessor.shutdown().orTimeout(30, TimeUnit.SECONDS).join();
eventProcessor.resetTokens().orTimeout(30, TimeUnit.SECONDS).join();
eventProcessor.start().orTimeout(30, TimeUnit.SECONDS).join();
```

Add `import java.util.concurrent.TimeUnit;` if absent. If existing code uses naked `.join()`, **upgrade** to `.orTimeout(...).join()` (default 30s) as part of this migration.

When the caller is itself async-capable (returns `CompletableFuture<?>` or composes via `thenCompose`), prefer chaining over blocking — keep the timeout at the outer caller.

### 6. Sweep imports / redundant fields

- Remove stale AF4 imports: `org.axonframework.config.*`, `org.axonframework.eventhandling.TrackingEventProcessor`, AF4-located `TokenStore` / `EventProcessor` / `StreamingEventProcessor`.
- Common AF4 shape injects **both** `EventProcessingConfiguration` and `TokenStore` (the latter for `fetchSegments` / `fetchToken`). AF5 routes both through `axonConfiguration.getOptionalComponent(TokenStore.class[, name])` — the separately injected `TokenStore` field is usually now redundant. Delete it (and constructor param) unless flagged out of scope.

## Verify

Invoke the external `axon4to5-isolatedtest` skill (see [../verification.md](../verification.md)):

```
Skill: axon4to5-isolatedtest
Inputs:
  target-name: <ClassSimpleName>
  build-file: <target>/pom.xml | <target>/build.gradle(.kts)
  main-sources:
    - src/main/java/<…>/<Class>.java
  test-sources:
    - src/test/java/<…>/<Class>Test.java        # omit (pass []) if no test class
  extra-deps:
    - org.axonframework:axon-messaging:${axon5.version}
    - org.axonframework:axon-configuration:${axon5.version}
  cleanup: false
```

## Examples

See [examples/01-heroes-stream-processors-operations.md](examples/01-heroes-stream-processors-operations.md) — Spring Boot ops endpoint that resets a stream processor by name.
