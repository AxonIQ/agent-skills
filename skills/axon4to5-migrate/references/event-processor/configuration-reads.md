# Event-processor configuration reads

Atomic migration of ONE class that **reads** AF4 `EventProcessingConfiguration` / `Configuration` to look up an event processor / token store / DLQ processor. Typically a Spring `@Component` ops endpoint (reset, replay, DLQ inspection).

## FQN cheat sheet

| AF4 (remove) | FQN |
|---|---|
| `Configuration` | `org.axonframework.config.Configuration` |
| `EventProcessingConfiguration` | `org.axonframework.config.EventProcessingConfiguration` |
| `TrackingEventProcessor` | `org.axonframework.eventhandling.TrackingEventProcessor` |
| `EventProcessor` / `StreamingEventProcessor` (AF4 loc.) | `org.axonframework.eventhandling.*` |
| `SequencedDeadLetterProcessor` | `org.axonframework.eventhandling.deadletter.SequencedDeadLetterProcessor` |
| `TokenStore` | `org.axonframework.eventhandling.tokenstore.TokenStore` |

| AF5 (add) | FQN |
|---|---|
| `AxonConfiguration` | `org.axonframework.common.configuration.AxonConfiguration` |
| `Configuration` (read-only) | `org.axonframework.common.configuration.Configuration` |
| `EventProcessor` | `org.axonframework.messaging.eventhandling.processing.EventProcessor` |
| `StreamingEventProcessor` | `org.axonframework.messaging.eventhandling.processing.streaming.StreamingEventProcessor` |
| `PooledStreamingEventProcessor` | `org.axonframework.messaging.eventhandling.processing.streaming.pooled.PooledStreamingEventProcessor` |
| `SubscribingEventProcessor` | `org.axonframework.messaging.eventhandling.processing.subscribing.SubscribingEventProcessor` |
| `SequencedDeadLetterProcessor` | `org.axonframework.messaging.eventhandling.deadletter.SequencedDeadLetterProcessor` |
| `TokenStore` | moved under `org.axonframework.eventstreaming.tokenstore.*` |

## Procedure

### Step 1 — Locate

```bash
grep -RlnE 'org\.axonframework\.config\.(Configuration|EventProcessingConfiguration)' --include='*.java' --include='*.kt' <target>/src
```

Pick a file using AF4 type for **read** ops on event-processor components (`eventProcessor`, `eventProcessorByProcessingGroup`, `tokenStore`, `sequencedDeadLetterProcessor`). Files touching only root buses / event store belong to the sibling `configuration-reads.md` of the relevant topic.

### Step 2 — Switch injected bean type

- Read-only (no lifecycle on root) → `Configuration`.
- Class touches root lifecycle (rare) → `AxonConfiguration`.
- AF4 injected `EventProcessingConfiguration` directly → switch to `AxonConfiguration` (entry point for module lookups).
- Rename field + constructor param (`eventProcessingConfiguration` → `axonConfiguration`).

- **Path A (Spring Boot):** `AxonConfiguration` auto-bean; constructor injection unchanged.
- **Path B (framework Configurer):** `config.getComponent(...)` or pass `AxonConfiguration` directly from `configurer.start()`.

### Step 3 — Rewrite lookups → AF5 two-step

Event-processor components live in **per-processor modules** named `"EventProcessor[<processorName>]"` (one per processor, NOT a single `"EventProcessing"` module).

| AF4 | AF5 |
|---|---|
| `epc.eventProcessor(name)` | `axonConfig.getModuleConfiguration("EventProcessor[" + name + "]").flatMap(m -> m.getOptionalComponent(EventProcessor.class))` |
| `epc.eventProcessor(name, EventProcessor.class)` | same as above with the specific type |
| `epc.eventProcessorByProcessingGroup(group)` | `getModuleConfiguration("EventProcessor[" + group + "]")…getOptionalComponent(EventProcessor.class)` |
| `epc.eventProcessorByProcessingGroup(group, StreamingEventProcessor.class)` | same with `StreamingEventProcessor.class` |
| `epc.tokenStore(processor)` | `getModuleConfiguration("EventProcessor[" + processor + "]")…getOptionalComponent(TokenStore.class)` |
| `epc.sequencedDeadLetterProcessor(group)` | `getModuleConfiguration("EventProcessor[" + group + "]")…getOptionalComponent(SequencedDeadLetterProcessor.class, "EventHandlingComponent[" + group + "][" + componentName + "]")` |

DLQ named-component lookup — the processor module typically holds many `SequencedDeadLetterProcessor`s (one per handling component). Disambiguate with the AF5 component name `"EventHandlingComponent[<processorName>][<componentName>]"`.

> **DLQ flag.** Read-side lookup compiles against free AF5. The underlying DLQ **store / wiring** (JPA dead-letter sequence, persistent DLQ beans) is Axoniq commercial. If the class also configures a DLQ impl, flag as commercial — belongs to a `axon4-to-axoniq5-*` recipe.

### Step 4 — Update component types

- `TrackingEventProcessor` → `StreamingEventProcessor` (and import). `TrackingEventProcessor` is **removed**.
- All processor types moved under `org.axonframework.messaging.eventhandling.processing.*`.
- AF4 specifically typed (`TrackingEventProcessor.class`) → broaden to `StreamingEventProcessor` (gets `supportsReset()`, `resetTokens()`, `start()`, `shutdown()` without committing to `PooledStreamingEventProcessor`).

### Step 5 — Adapt async lifecycle / DLQ calls

AF4 sync → AF5 async. Return type `void` → `CompletableFuture<Void>`:
- `processor.start()`, `shutdown()` (renamed from AF4 `shutDown()` — capital `D` → lowercase), `resetTokens()`, DLQ `processAny()`, DLQ `process(...)`.

Bridge with `.orTimeout(<d>, <u>).join()` (never naked `.join()` / `.get()`):

```java
eventProcessor.shutdown().orTimeout(30, TimeUnit.SECONDS).join();
eventProcessor.resetTokens().orTimeout(30, TimeUnit.SECONDS).join();
eventProcessor.start().orTimeout(30, TimeUnit.SECONDS).join();
```

If existing code has naked `.join()`, **upgrade** to `.orTimeout(...).join()` (default 30s). When caller is async-capable, prefer chaining over blocking.

### Step 6 — Sweep

- Remove stale AF4 imports: `org.axonframework.config.*`, AF4-located `TrackingEventProcessor`, `TokenStore`, `EventProcessor`, `StreamingEventProcessor`.
- AF4 commonly injected both `EventProcessingConfiguration` and `TokenStore` — AF5 routes both through `axonConfiguration.getOptionalComponent(TokenStore.class[, name])`. Delete the separately injected `TokenStore` field + constructor param unless flagged out of scope.

## Verify

`axon4to5-isolatedtest` with:
```
target-name: <ClassSimpleName>
main-sources: [<Class>.java]
test-sources: [<Class>Test.java] # or []
extra-deps: [axon-messaging, axon-configuration]
```
