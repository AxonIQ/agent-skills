---
id: event-processor
title: Event Processor
description: Migrates a single Axon Framework 4 event-handling component (projector / event processor) to Axon Framework 5 — annotations, imports, sequencing policy, async dispatch, and processor configuration via `EventProcessorDefinition`.
order: 2
argument-hint: $SOURCE
---

# Event Processor

> Single AF4 event-handling component → AF5 message handler. Same architecture, no DCB. Annotations move packages, `@ProcessingGroup` becomes `@Namespace`, in-handler dispatch swaps `CommandGateway` field for `CommandDispatcher` method parameter, sequencing policy moves from YAML to class-level `@SequencingPolicy`, and processor wiring (when in scope) uses `EventProcessorDefinition` (Spring Path A) or `MessagingConfigurer.eventProcessing(...)` (native Path B) — never the AF4 `registerPooledStreamingEventProcessor(...)` form.

## Source

- `$SOURCE` (required) — FQN, file path, or simple class name of an AF4 event-handling component. The class is annotated `@ProcessingGroup` (typical) AND/OR carries at least one `@EventHandler` method. After OpenRewrite Phase 1 it may already be partially migrated (e.g. `@Namespace` swapped but `@MetaDataValue` not).

## Scope

- `$SOURCE` class itself.
- Every event class referenced by `@EventHandler` first-parameter types on `$SOURCE` (read-only — events are NOT mutated by this recipe; the aggregate recipe owns event-shape changes via `@EventTag`).
- Sibling annotations on the same class — `@DisallowReplay`, `@ResetHandler`, `@MetaDataValue` parameters.
- For projectors that dispatch commands (have a `CommandGateway` field): the gateway field declaration + every call site inside `@EventHandler` bodies (signature swap + async chaining).
- The custom `SequencingPolicy` implementation when one is referenced by external YAML / `@Bean` and the class needs `@SequencingPolicy` to preserve behaviour (see Step 7).
- The Configurer / `@Configuration` wiring file ONLY when processor configuration is in scope (in-progress recipe state — see Step 11). Typical filenames: `*Configuration`, `AxonConfig`, `*Application` (`.java` or `.kt`). Only the `@Bean EventProcessorDefinition` / `MessagingConfigurer.eventProcessing(...)` slice for `$SOURCE` — not every processor in the project.
- `application.yaml` / `application.properties` for the per-processor `sequencing-policy` key (deleted as it moves to the class) and for the `serializer:` → `converter:` rename.
- **EventProcessingConfiguration config-reader companions** — during Research: `grep -RlnE 'EventProcessingConfiguration|epc\.eventProcessor\(|eventProcessorByProcessingGroup' --include='*.java' --include='*.kt' <project>/src`. Filter matches for those referencing `$SOURCE`'s `@ProcessingGroup` / `@Namespace` string. Ops endpoints (reset/replay/DLQ controllers) are the most common shape. Add them to scope.

Scope grows during FLOW.md Research; it never shrinks. Sibling event-handling components, aggregates, sagas, application beans unrelated to `$SOURCE` are NEVER in scope.

## Applicable

Surface check on `$SOURCE` before Research. Cheap reads only — annotations, presence of method-level markers.

Decision rule (top-down; first match wins):

1. **Saga** — class annotated `@Saga` OR any method annotated `@SagaEventHandler` / `@StartSaga` / `@EndSaga`. → **Rejected** with NOTES naming `saga` (route to saga recipe).
2. **Aggregate** — class annotated `@Aggregate` / `@AggregateRoot` AND has at least one `@EventSourcingHandler` (not `@EventHandler`). → **Rejected** with NOTES naming `aggregate` (route to aggregate recipe).
3. **Event-handling component, AF4 shape** — class has at least one `@EventHandler` method AND class-level `@ProcessingGroup` annotation. → **continue** to Research.
4. **Event-handling component, partially-migrated** — class has at least one `@EventHandler` method AND class-level `@Namespace` annotation (already swapped). → **continue** to Research; the Success Criteria pre-Apply check decides idempotent-Success vs. continue.
5. **Event-handling component, no `@ProcessingGroup`/`@Namespace`** — class has `@EventHandler` but no group/namespace marker. → **continue** with NOTES surfacing the missing namespace (recipe will use the class FQN's package as a default and emit a Learning).
6. **EventProcessingConfiguration reader** — no `@EventHandler` anywhere, but imports `org.axonframework.config.EventProcessingConfiguration` OR calls `epc.eventProcessor(...)` / `eventProcessorByProcessingGroup(...)` / `epc.tokenStore(...)` / `epc.sequencedDeadLetterProcessor(...)`. → **continue** as config-reader target (Toolbox Step 12).
7. **None of the above** — no `@EventHandler` method, no `EventProcessingConfiguration` pattern. → **Rejected** with NOTES naming the failed predicate.

## Blocker

Constructs the recipe cannot migrate on its own.

**Emission model — all blockers at once.** Scans every blocker during Research (FLOW.md S3) BEFORE the Plan-Apply loop. On any detection, emits **one** Blocker result enumerating every detected blocker with its Options sub-block. Caller resolves each (edits code, removes constructs, redesigns wiring) and re-invokes; the recipe re-scans, blockers that no longer match disappear, and the recipe proceeds when none remain.

### B1 — MongoTokenStore

`MongoTokenStore` (`org.axonframework.extensions.mongo.eventhandling.tokenstore.MongoTokenStore`) registered for the processor. AF5 has no `axon-mongo` release; the AF4 extension is end-of-life. Detect with `grep -RnE 'MongoTokenStore|org\.axonframework\.extensions\.mongo' <project>` plus per-processor YAML/property lookups (`axon.eventhandling.processors.<group>.token-store`). The recipe halts because switching the token store has data consequences (the AF4 Mongo collection is not readable by `JpaTokenStore`; the caller must decide between replay-from-event-store and a manual data migration).

### B2 — Axon-Kafka extension on this component

`KafkaPublisher`, `StreamableKafkaMessageSource`, `KafkaMessageSourceConfigurer`, or any import under `org.axonframework.extensions.kafka` on or near `$SOURCE`. No AF5 release of the Kafka extension yet. Detect with `grep -RnE 'org\.axonframework\.extensions\.kafka|KafkaPublisher|StreamableKafkaMessageSource' <aggregate file> <aggregate package>`. The caller decides whether to leave the Kafka source on AF4 deps, redesign the integration, or remove the feature.

### B3 — `SagaEventHandler` mistakenly placed on this class

`@SagaEventHandler` on a method of `$SOURCE` while the class is otherwise event-processor-shaped (carries `@ProcessingGroup`). Usually a real saga that was wrongly classified — emits Blocker for caller routing instead of silently corrupting the saga state machine.

### B4 — `QueryUpdateEmitter` field-injected on `$SOURCE`

AF5 enforces `QueryUpdateEmitter` as a **method parameter** (see [projectors-event-processors.adoc](../../docs/paths/projectors-event-processors.adoc) § `QueryUpdateEmitter` as a parameter). Field-injecting it AF4-style is unsupported; the recipe halts because rewriting the field to per-method injection touches every `@EventHandler` body and may need follow-up edits in the corresponding query-result subscribers — outside the strict event-processor migration mechanics.

### Unmet project prerequisites

- Project does not compile pre-recipe — the `axon4to5-isolatedtest` Skill cannot establish a baseline. Surface as Blocker `prerequisite-not-compiling`.

### Flagged (not Blocker) — Dead-Letter Queue presence

If `$SOURCE`'s processing group has a DLQ wired (`registerDeadLetterQueue*` or `axon.eventhandling.processors.<group>.dlq.*` in YAML), the recipe does NOT block, but emits a Learning in Result NOTES naming the DLQ class / config key. DLQ migration is out of scope of THIS recipe — schema changes documented in [dlq.adoc](../../docs/paths/dlq.adoc) and the commercial `axoniq-dead-letter` feature live in a separate recipe.

## Out of Scope

- Sibling event-handling components, aggregates, sagas.
- Other processors' configuration (only `$SOURCE`'s processor definition is in scope when present).
- `SequencedDeadLetterQueue` / DLQ implementation rewrite — flag only.
- Token store schema migration (AF4 → AF5 Mongo → Jpa).
- Event-shape changes (`@EventTag`, `@Event(version=…)`, `TargetEntityId`) — owned by the aggregate recipe.
- DCB introduction or alternative processor types invented from scratch.
- `MessageHandlerInterceptor` / `@EventHandlerInterceptor` rewrites — flag only.
- Logging changes, package renames, formatting changes.

## References

Inherits the catalog baseline (see DEFAULT.md § Toolbox baseline). Recipe-specific entries — each is a markdown link with apply-condition:

- [projectors-event-processors.adoc](../../docs/paths/projectors-event-processors.adoc) — *apply-condition:* always. Covers `@EventHandler` import move, `@ProcessingGroup` → `@Namespace`, `TrackingEventProcessor` removal, `EventProcessorDefinition` (Spring) and `MessagingConfigurer.eventProcessing(...)` (native).
- [sequencing-policies.adoc](../../docs/paths/sequencing-policies.adoc) — *apply-condition:* scope contains a custom `SequencingPolicy` implementation OR the project's YAML declares `axon.eventhandling.processors.<group>.sequencing-policy` OR the AF4 wiring used a `@Bean SequencingPolicy`.
- [dlq.adoc](../../docs/paths/dlq.adoc) — *apply-condition:* `$SOURCE`'s processing group has a DLQ wired (informational only — recipe flags, does not migrate).
- [messages.adoc](../../docs/paths/messages.adoc) — *apply-condition:* always. Covers the `@MetaDataValue` → `@MetadataValue` capitalisation flip and `getPayload()` / `getMetaData()` → `payload()` / `metaData()` accessor rename.
- [interceptors.adoc](../../docs/paths/interceptors.adoc) — *apply-condition:* `$SOURCE` carries `@EventHandlerInterceptor` or `MessageHandlerInterceptor` — informational only (recipe flags, does not migrate).
- [configuration.adoc](../../docs/paths/configuration.adoc) — *apply-condition:* `configuration=native` AND the project's Configurer file is in scope for processor wiring.

## Success Criteria

Extends DEFAULT.md baseline. DEFAULT's three baseline criteria (compile-clean, tests green via `axon4to5-isolatedtest`, no silent behavioural regressions) stay in force. Recipe adds:

### Recipe-specific structural invariants

For every file in `# Scope`:

1. **No AF4 imports survive** on `$SOURCE`. None of the following substrings appears in the source file:
   - `org.axonframework.config.ProcessingGroup`
   - `org.axonframework.eventhandling.EventHandler` (the `import` line)
   - `org.axonframework.eventhandling.DisallowReplay`
   - `org.axonframework.eventhandling.ResetHandler`
   - `org.axonframework.messaging.annotation.MetaDataValue` (AF4 capital-D import)
   - `org.axonframework.commandhandling.gateway.CommandGateway` (only when this class dispatches in-handler; top-of-chain controllers/REST APIs keep `CommandGateway` per the command-gateway recipe)
   - `org.axonframework.eventhandling.async.SequencingPolicy` (AF4 SequencingPolicy import)

2. **`@Namespace` present at class level** with the same string the AF4 `@ProcessingGroup` carried (or, when `@ProcessingGroup` was absent, a string consistent with the project's external references). Import: `org.axonframework.messaging.core.annotation.Namespace`.

3. **AF5 handler annotation imports** present where used:
   - `org.axonframework.messaging.eventhandling.annotation.EventHandler` (always for this recipe)
   - `org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay` (when source uses it)
   - `org.axonframework.messaging.eventhandling.replay.annotation.ResetHandler` (when source uses it)
   - `org.axonframework.messaging.core.annotation.MetadataValue` — note capital-D **and** the `.core.` package; AF4 was `@MetaDataValue` from `messaging.annotation`. Case matters: `@MetaDataValue` (AF4) must NOT remain after migration.

4. **In-handler command dispatch (when applicable)** — if `$SOURCE` had a `CommandGateway` field plus `commandGateway.send(...)` / `sendAndWait(...)` inside an `@EventHandler`:
   - The class-level `CommandGateway` field is removed.
   - Every affected `@EventHandler` receives `CommandDispatcher commandDispatcher` as a method parameter (`org.axonframework.messaging.commandhandling.gateway.CommandDispatcher`).
   - Every `sendAndWait(...)` call is rewritten to async `commandDispatcher.send(...).getResultMessage()` (chained via `.thenApply` / `.thenCompose` / `.exceptionallyCompose` as needed). The handler method's return type becomes `CompletableFuture<?>` (or a narrower future type when downstream callers require it). `java.util.concurrent.CompletableFuture` import added.

5. **`@SequencingPolicy` annotation present when behaviourally required** — if the AF4 wiring declared a custom sequencing policy for `$SOURCE`'s processing group (via `@Bean SequencingPolicy`, `EventProcessingConfigurer.registerSequencingPolicy(...)`, or YAML `axon.eventhandling.processors.<group>.sequencing-policy`), the migrated class carries an equivalent `@SequencingPolicy(type = <Policy>.class, parameters = …)` at the class level. Built-in policy classes (`MetadataSequencingPolicy`, `SequentialPerAggregatePolicy`, `SequentialPolicy`, `FullConcurrencyPolicy`) are reused; custom policies are migrated by Step 7's body-level rewrite.

6. **Processor wiring (when in scope)** — if the AF4 `@Bean ConfigurerModule` or native Configurer block registered `$SOURCE`'s processor via `registerPooledStreamingEventProcessor(...)` / `registerSubscribingEventProcessor(...)`:
   - **Path A — `configuration=spring`**: replaced by a `@Bean EventProcessorDefinition` of shape `EventProcessorDefinition.pooledStreaming("<namespace>") .assigningHandlers(...) .customized(...)` (import `org.axonframework.extension.spring.config.EventProcessorDefinition`).
   - **Path B — `configuration=native`**: replaced by `configurer.eventProcessing(eventProcessing -> eventProcessing.pooledStreaming(...).processor("<namespace>", module -> module.eventHandlingComponents(...) ...))` — via `MessagingConfigurer.eventProcessing(...)`. The AF4 `EventProcessingConfigurer.registerPooledStreamingEventProcessor(...)` call MUST NOT survive.

7. **YAML / properties** — when `application.yaml` is in scope:
   - `axon.eventhandling.processors.<group>.sequencing-policy` key REMOVED (moved to class-level annotation per (5)).
   - `axon.eventhandling.processors.<group>.mode: tracking` rewritten to `mode: pooled` (AF5 has no `TrackingEventProcessor`).
   - Global `axon.serializer.*` → `axon.converter.*` (recipe handles only the slice in scope; full conversion belongs to the serializer recipe).

8. **Config-reader migration (when in scope)** — when an `EventProcessingConfiguration` config-reader class is in scope: no `org.axonframework.config.EventProcessingConfiguration` or `org.axonframework.config.Configuration` import; lookups use two-step `getModuleConfiguration("EventProcessor[" + name + "]").flatMap(...)` form; no `TrackingEventProcessor` reference; async lifecycle calls (`start`, `shutdown`, `resetTokens`, `processAny`, `process`) wrapped with `.orTimeout(...).join()` at synchronous boundaries.

Aggregation rule: **all match (AND)** — DEFAULT.md baseline AND this section's checks.

### Verification

Use the `axon4to5-isolatedtest` Skill per DEFAULT.md § Verification. `target-name` is the simple class name of `$SOURCE`. `main-sources` enumerate every file in `# Scope`. `test-sources` enumerate `<target>Test` and direct subclass tests when present.

`extra-deps` baseline: `org.axonframework:axon-messaging`, `org.axonframework:axon-eventhandling`. Add `org.axonframework.extensions.spring:axon-spring-boot-starter` (or the commercial `io.axoniq.framework:…` coordinate when `framework=axoniq`) for `configuration=spring`.

## Toolbox

### Common steps (always — both paths)

*Apply-condition:* always.

1. **Class-level `@ProcessingGroup` → `@Namespace`** (same string argument). Replace import `org.axonframework.config.ProcessingGroup` with `org.axonframework.messaging.core.annotation.Namespace`. The string is the **binding contract**: it must match every external reference (YAML `axon.eventhandling.processors.<string>.*`, `EventProcessorDefinition.pooledStreaming("<string>")`, `MessagingConfigurer.eventProcessing(...).processor("<string>", …)`). Mismatch silently drops events at runtime — there is no compile-time signal.
2. **Sibling annotation imports** — for every method-level annotation in scope, swap to its AF5 location:
   - `@EventHandler` → `org.axonframework.messaging.eventhandling.annotation.EventHandler`.
   - `@DisallowReplay` → `org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay`.
   - `@ResetHandler` → `org.axonframework.messaging.eventhandling.replay.annotation.ResetHandler`.
   - `@MetaDataValue` (AF4, capital-D `D`) → `@MetadataValue` (AF5, capital `M` lower `d`) at `org.axonframework.messaging.core.annotation.MetadataValue`. **Case-sensitive — typos silently no-op.**
3. **Accessor renames inside handler bodies** — `event.getPayload()` → `event.payload()`, `event.getMetaData()` → `event.metaData()`. AF5 events are records with accessor methods, not getter-style.

### Step 4 — In-handler command dispatch (CommandGateway → CommandDispatcher)

*Apply-condition:* `$SOURCE` has a class-level `CommandGateway` field AND at least one `@EventHandler` body that calls it.

1. Remove the class-level `CommandGateway` field and its constructor injection.
2. For every `@EventHandler` method that uses the gateway, add `CommandDispatcher commandDispatcher` as a method parameter (`org.axonframework.messaging.commandhandling.gateway.CommandDispatcher`). The framework binds this parameter to the active `ProcessingContext` automatically.
3. Rewrite every `commandGateway.sendAndWait(cmd)` to async: `commandDispatcher.send(cmd, metadata).getResultMessage()` returning `CompletableFuture<? extends Message>`. The method's return type becomes `CompletableFuture<?>` (or a narrower future). Add `import java.util.concurrent.CompletableFuture;`.
4. Try/catch around the AF4 blocking `sendAndWait` (typically compensation logic) becomes `.exceptionallyCompose(error -> …)` on the future chain. Conditional dispatch becomes `.thenCompose(...)` / early-returns via `CompletableFuture.completedFuture(null)`.
5. **Do not** keep `CommandGateway` AND introduce `CommandDispatcher` side-by-side. Pick one based on call-site context: in-handler ⇒ `CommandDispatcher`; top-of-chain (REST controller, CLI, MCP tool) ⇒ keep `CommandGateway` (owned by the command-gateway recipe, out of scope here).

### Step 5 — `@MetadataValue` casing flip (capital-D loss)

*Apply-condition:* `$SOURCE` uses `@MetaDataValue` on any handler parameter.

The AF4 annotation `@MetaDataValue` has capital `D`: `MetaData`. AF5's `@MetadataValue` has only the leading `M` capitalised: `Metadata`. Both the symbol AND the import package change:

- AF4 import: `org.axonframework.messaging.annotation.MetaDataValue`
- AF5 import: `org.axonframework.messaging.core.annotation.MetadataValue`

Typos compile but silently no-op (the parameter receives `null`). Grep before and after the rewrite to confirm the AF4 form is fully gone.

### Step 6 — `@SequencingPolicy` class-level annotation (YAML / @Bean → annotation)

*Apply-condition:* the AF4 wiring referenced a sequencing policy for `$SOURCE`'s processing group — either via a `@Bean SequencingPolicy` registered with `EventProcessingConfigurer.registerSequencingPolicy(...)` / `assignSequencingPolicy(...)`, or via YAML `axon.eventhandling.processors.<group>.sequencing-policy`.

1. Annotate `$SOURCE`'s class with `@SequencingPolicy(type = <PolicyClass>.class, parameters = "<param>")` (`org.axonframework.messaging.core.annotation.SequencingPolicy`).
2. Built-in policy classes (no body migration needed):
   - `MetadataSequencingPolicy.class` with `parameters = "<metadataKey>"` — the AF4 idiom of "sequence by a metadata key" (very common; legacy projects often had a per-tenant `@Bean SequencingPolicy` reading e.g. `GameMetaData.GAME_ID_KEY`).
   - `SequentialPerAggregatePolicy.class` — AF4 default; rarely needs to be explicit.
   - `SequentialPolicy.class` — DCB default.
   - `FullConcurrencyPolicy.class` — no sequencing.
3. **Custom policies** — see Step 7.
4. Remove the corresponding YAML key `axon.eventhandling.processors.<group>.sequencing-policy` (Step 8).
5. The `@Bean SequencingPolicy` definition itself is NOT deleted by this recipe (other processors may share it). Leave the bean in place; flag in Result NOTES if it becomes orphan after the migration is complete.

### Step 7 — Custom `SequencingPolicy` implementation rewrite

*Apply-condition:* the project ships a custom class implementing `org.axonframework.eventhandling.async.SequencingPolicy<EventMessage<?>>` that `$SOURCE` depends on.

1. Swap the implemented interface to `org.axonframework.messaging.core.sequencing.SequencingPolicy` (no generic parameter — AF5 binds it through `EventMessage<?>` at registration time).
2. Method rename + signature change: AF4 `Object getSequenceIdentifierFor(EventMessage<?> event)` becomes AF5 `Optional<Object> sequenceIdentifierFor(EventMessage<?> message, ProcessingContext context)`.
3. Accessor renames inside the body: `event.getPayload()` → `event.payload()`, `event.getMetaData()` → `event.metaData()` (or `message.metaData()` using the new parameter name).
4. Return wrapping: every `return value;` becomes `return Optional.ofNullable(value);`; every `return null;` becomes `return Optional.empty();`.

### Step 8 — YAML / properties (when application.yaml is in scope)

*Apply-condition:* `application.yaml` / `application.properties` exists in the working tree AND has `axon.*` keys related to `$SOURCE`'s processor.

1. Delete `axon.eventhandling.processors.<group>.sequencing-policy` (moved to class-level annotation in Step 6).
2. Rewrite `axon.eventhandling.processors.<group>.mode: tracking` → `mode: pooled` (`TrackingEventProcessor` removed in AF5; `PooledStreamingEventProcessor` is the direct replacement).
3. Rewrite `axon.serializer.*` → `axon.converter.*` (only the slice in scope — the project-wide rename is the serializer recipe's job; surface the broader rewrite as a Learning).
4. Per-processor `thread-count`, `batch-size`, `initial-segment-count` keys carry over unchanged — same key shape under the AF5 `axon.eventhandling.processors.<group>.*` namespace.

### Step 9 — Spring processor wiring (Path A — `EventProcessorDefinition`)

*Apply-condition:* `configuration=spring` AND the project's `@Configuration` class registers `$SOURCE`'s processor (via `EventProcessingConfigurer.registerPooledStreamingEventProcessor(...)`, `registerSubscribingEventProcessor(...)`, or `assignHandlerTypesMatching(...)` for the matching group).

Replace the AF4 `@Bean ConfigurerModule` body with an AF5 `@Bean EventProcessorDefinition`. The new bean owns processor type (pooled / subscribing), the handler matcher, and the customisation block. The AF4 `EventProcessingConfigurer` API is gone.

Required form:

```java
import org.axonframework.extension.spring.config.EventProcessorDefinition;

@Bean
public EventProcessorDefinition <bean-name>() {
    return EventProcessorDefinition.pooledStreaming("<namespace>")
                                   .assigningHandlers(descriptor -> descriptor.beanType().getPackageName()
                                                                              .startsWith("<package>"))
                                   .customized(config -> config.initialSegmentCount(<n>)
                                                               .batchSize(<n>));
}
```

For subscribing processors, use `EventProcessorDefinition.subscribing("<namespace>")` instead. The `.customized(...)` block is optional — drop it when there were no AF4 customisations.

### Step 10 — Native processor wiring (Path B — `MessagingConfigurer.eventProcessing(...)`)

*Apply-condition:* `configuration=native` AND the project's Configurer file registers `$SOURCE`'s processor.

Replace the AF4 `EventProcessingConfigurer.registerPooledStreamingEventProcessor(...)` chain with the AF5 `MessagingConfigurer.eventProcessing(...)` fluent block. The AF4 `EventProcessingModule` is gone.

Required form:

```java
public void configure(MessagingConfigurer configurer) {
    configurer.eventProcessing(eventProcessing ->
        eventProcessing.pooledStreaming(pooledStreaming ->
            pooledStreaming.processor("<namespace>", module ->
                module.eventHandlingComponents(components ->
                          components.autodetected(cfg -> new <SourceClass>(cfg.getComponent(<Dep>.class)))
                      )
                      .customized((cfg, conf) -> conf.batchSize(<n>).initialSegmentCount(<n>))
            )
        )
    );
}
```

For subscribing processors, swap `pooledStreaming(...)` for `subscribing(...)`. Drop `.customized(...)` when no AF4 customisations existed.

### Step 11 — `QueryUpdateEmitter` field → method parameter

*Apply-condition:* `$SOURCE` has a `QueryUpdateEmitter` field (typically `@Autowired`).

AF5 enforces `QueryUpdateEmitter` as a parameter of message handlers. Remove the class-level field and its constructor/setter injection. Add `QueryUpdateEmitter emitter` as a parameter on every `@EventHandler` method that calls it. (Same import in AF5 as AF4: `org.axonframework.queryhandling.QueryUpdateEmitter` — the API location stayed; only the injection style changed.)

### Step 12 — EventProcessingConfiguration config-reader migration

*Apply-condition:* `$SOURCE` matched Applicable predicate 6 OR Research found a companion config-reader class in scope.

**Path A (Spring Boot):** `AxonConfiguration` is auto-created as a Spring bean; constructor injection / `@Autowired` unchanged.
**Path B (native Configurer):** pass the live `AxonConfiguration` from `configurer.start()` as a constructor argument.

1. **Switch injected type** — `EventProcessingConfiguration` → `AxonConfiguration` (`org.axonframework.common.configuration.AxonConfiguration`). If the class only reads and never touches root lifecycle, `Configuration` (`org.axonframework.common.configuration.Configuration`) is sufficient; prefer `AxonConfiguration` when `EventProcessingConfiguration` was the original type. Rename the field accordingly (`eventProcessingConfiguration` → `axonConfiguration`).

2. **Rewrite event-processor lookups — two-step via module name**:

Module name convention: `"EventProcessor[" + processorName + "]"` (case-sensitive; matches `@Namespace` / `@ProcessingGroup` string exactly).

| AF4 call | AF5 replacement |
|---|---|
| `epc.eventProcessor(name)` | `axonConfig.getModuleConfiguration("EventProcessor[" + name + "]").flatMap(m -> m.getOptionalComponent(EventProcessor.class))` |
| `epc.eventProcessor(name, EventProcessor.class)` | same as above |
| `epc.eventProcessorByProcessingGroup(group)` | `axonConfig.getModuleConfiguration("EventProcessor[" + group + "]").flatMap(m -> m.getOptionalComponent(EventProcessor.class))` |
| `epc.eventProcessorByProcessingGroup(group, StreamingEventProcessor.class)` | `axonConfig.getModuleConfiguration("EventProcessor[" + group + "]").flatMap(m -> m.getOptionalComponent(StreamingEventProcessor.class))` |
| `epc.tokenStore(processor)` | `axonConfig.getModuleConfiguration("EventProcessor[" + processor + "]").flatMap(m -> m.getOptionalComponent(TokenStore.class))` |
| `epc.sequencedDeadLetterProcessor(group)` | `axonConfig.getModuleConfiguration("EventProcessor[" + group + "]").flatMap(m -> m.getOptionalComponent(SequencedDeadLetterProcessor.class, "EventHandlingComponent[" + group + "][" + componentName + "]"))` |

DLQ flag: `SequencedDeadLetterProcessor` lookup compiles against free AF5 (`org.axonframework.messaging.eventhandling.deadletter`), but the underlying DLQ store is Axoniq commercial. If the class also instantiates / configures a DLQ implementation, flag it — that part belongs to a commercial recipe.

3. **Update component types** — `TrackingEventProcessor` → `StreamingEventProcessor` (AF5 FQN: `org.axonframework.messaging.eventhandling.processing.streaming.StreamingEventProcessor`). `TrackingEventProcessor` is removed in AF5.

4. **Adapt async lifecycle** — AF4 sync → AF5 `CompletableFuture<Void>`. Bridge with `.orTimeout(30, TimeUnit.SECONDS).join()` at synchronous call sites. Never bare `.join()` / `.get()` without a preceding `.orTimeout(...)`.

   | AF4 | AF5 |
   |---|---|
   | `processor.start()` | `processor.start()` → `CompletableFuture<Void>` |
   | `processor.shutDown()` | `processor.shutdown()` (lowercase d) → `CompletableFuture<Void>` |
   | `processor.resetTokens()` | `processor.resetTokens()` → `CompletableFuture<Void>` |
   | `dlq.processAny()` | `dlq.processAny()` → `CompletableFuture<Void>` |
   | `dlq.process(...)` | `dlq.process(...)` → `CompletableFuture<Void>` |

   Add `import java.util.concurrent.TimeUnit;` if absent. When caller is async-capable, prefer chaining over blocking.

5. **Sweep imports** — remove `org.axonframework.config.*`, `org.axonframework.eventhandling.TrackingEventProcessor`, AF4-located `TokenStore` / `EventProcessor` / `StreamingEventProcessor`. Add AF5 equivalents from `org.axonframework.messaging.eventhandling.processing.*` and `org.axonframework.common.configuration.*`.
   - If class had a separately injected `TokenStore` field: remove it — route through `axonConfiguration.getModuleConfiguration(...).flatMap(m -> m.getOptionalComponent(TokenStore.class))` instead.

## Use cases

Each entry is a markdown link to the full before/after example, followed by its apply-condition.

- [01-pure-projector-spring.md](use-cases/01-pure-projector-spring.md) — *apply-condition:* `configuration=spring` AND `$SOURCE` has only `@EventHandler` / `@ResetHandler` methods (no `CommandGateway` field, no in-handler dispatch).
- [02-projector-with-command-dispatch.md](use-cases/02-projector-with-command-dispatch.md) — *apply-condition:* `$SOURCE` injects a `CommandGateway` field AND dispatches commands in `@EventHandler` bodies (typical "automation" or "process manager" shape).
- [03-yaml-to-sequencing-policy.md](use-cases/03-yaml-to-sequencing-policy.md) — *apply-condition:* `application.yaml` declares `axon.eventhandling.processors.<group>.sequencing-policy` for `$SOURCE`'s group OR a `@Bean SequencingPolicy` is registered via `EventProcessingConfigurer.assignSequencingPolicy(...)`.
- [04-event-processor-definition-spring.md](use-cases/04-event-processor-definition-spring.md) — *apply-condition:* `configuration=spring` AND the project's `@Configuration` has an AF4 `@Bean ConfigurerModule` that calls `registerPooledStreamingEventProcessor(...)` / `assignHandlerTypesMatching(...)` for `$SOURCE`'s group.
- [05-native-configurer-event-processing.md](use-cases/05-native-configurer-event-processing.md) — *apply-condition:* `configuration=native` AND the project's Configurer block calls `configurer.eventProcessing().registerPooledStreamingEventProcessor(...)`.
- [06-custom-sequencing-policy-rewrite.md](use-cases/06-custom-sequencing-policy-rewrite.md) — *apply-condition:* scope contains a class implementing the AF4 `SequencingPolicy<EventMessage<?>>` interface that `$SOURCE` depends on.
- [07-dual-role-event-and-query-handler.md](use-cases/07-dual-role-event-and-query-handler.md) — *apply-condition:* `$SOURCE` has BOTH `@EventHandler` AND `@QueryHandler` methods (the query-handler recipe's annotation moves apply in tandem with this recipe's `@Namespace` / `@SequencingPolicy` moves).
- [08-rejected-aggregate.md](use-cases/08-rejected-aggregate.md) — *apply-condition:* `$SOURCE` is annotated `@Aggregate` / `@AggregateRoot` (predicate 2 fires; route to aggregate recipe).

## Gotchas

- **`@Namespace` string is a binding contract.** It must match the AF4 `@ProcessingGroup` value exactly AND every external reference — YAML `axon.eventhandling.processors.<string>.*`, `EventProcessorDefinition.pooledStreaming("<string>")`, `MessagingConfigurer.eventProcessing(...).processor("<string>", …)`. Mismatch silently drops events at runtime; there is no compile signal. After renaming, grep the repo for the OLD group string to verify zero stragglers.
- **`@MetaDataValue` (AF4) vs `@MetadataValue` (AF5)** — capital `D` only on the AF4 form. The annotation symbol AND the import package change. Typos compile cleanly and the parameter silently receives `null` at runtime. Always grep for the AF4 form after the rewrite to confirm zero remain.
- **`sendAndWait` → `getResultMessage()` is not just an API swap.** AF4 `sendAndWait` blocked + threw on failure; AF5 `send(...).getResultMessage()` returns `CompletableFuture<? extends Message>` and the failure surfaces on the future, not in the try-block. AF4 try/catch compensation paths silently stop compensating. Use `.exceptionallyCompose(error -> commandDispatcher.send(<compensation>).resultAs(Message.class))`. If you must pass `getResultMessage()` into `exceptionallyCompose`, add `.thenApply(m -> (Message) m)` before the `exceptionallyCompose` call — the wildcard `? extends Message` is not assignable to the `CompletionStage<Message>` type parameter that `exceptionallyCompose` expects. **Prefer `.resultAs(Message.class)` over `.getResultMessage()` in lambda positions** — it returns `CompletableFuture<Message>` (no wildcard) and avoids the cast entirely.
- **`org.axonframework.messaging.core.Message` is NOT generic in AF5.** Declared as `public interface Message`. Code that uses `CompletableFuture<? extends Message<?>>` (with the `<?>`) does not compile. The correct shape is `CompletableFuture<? extends Message>`.
- **Don't use `EventProcessorDefinition` and the AF4 `EventProcessingConfigurer` side-by-side.** Spring picks up the AF5 `@Bean EventProcessorDefinition` first; a stale AF4 `@Bean ConfigurerModule` that still references `EventProcessingConfigurer.registerPooledStreamingEventProcessor(...)` will fail at startup or be silently shadowed. Delete the AF4 wiring as part of the same commit.
- **`TrackingEventProcessor` is gone.** YAML `mode: tracking` must be rewritten to `mode: pooled` — see Step 8.
- **`@Bean SequencingPolicy` may be shared.** If multiple processors reference it via `assignSequencingPolicy(...)`, the recipe migrates ONLY `$SOURCE`'s reference (Step 6) and leaves the bean in place. After all dependent processors are migrated, the bean becomes orphan — flag in NOTES, but do NOT delete (out of scope for this recipe).
- **`@ResetHandler` migration is purely an import swap** (`org.axonframework.eventhandling.ResetHandler` → `org.axonframework.messaging.eventhandling.replay.annotation.ResetHandler`). Body unchanged.
- **DLQ presence is informational.** Do not attempt to migrate `SequencedDeadLetterQueue` / `registerDeadLetterQueue*` references. Flag in Result NOTES and route to the commercial `axoniq-dead-letter` flow per [dlq.adoc](../../docs/paths/dlq.adoc).
- **OpenRewrite Phase 1 quirks** — typically swaps `@ProcessingGroup` → `@Namespace` annotation only (string preserved). Often leaves AF4 `@EventHandler` import, AF4 `@MetaDataValue`, and the AF4 `CommandGateway` field in place. Predicate 4 in `# Applicable` handles this partially-migrated state — the Success Criteria pre-Apply check fails on the surviving AF4 imports and Plan-Apply finishes the work.
- **Config-reader: module name is case-sensitive** — `"EventProcessor[" + processorName + "]"` must match the `@Namespace` string exactly. A mismatch returns `Optional.empty()` at runtime with no error; the ops call silently no-ops. Grep the processor name from `$SOURCE`'s `@Namespace` annotation before constructing the module name.
- **Config-reader: `shutDown` → `shutdown`** — AF4 method had capital `D`; AF5 is lowercase. Both compile if the project also has a `shutdown()` method — easy to miss. Grep for `shutDown` before and after to confirm the old form is gone.
- **Config-reader: separately injected `TokenStore` usually becomes redundant** — AF4 often injected both `EventProcessingConfiguration` and `TokenStore`. After migrating to `getModuleConfiguration(...)`, the `TokenStore` field is typically no longer needed. Delete it (and its constructor parameter) unless flagged out of scope.
- **`@SequencingPolicy` package is `core.annotation`, NOT `core.sequencing.annotation`.** The correct import is `org.axonframework.messaging.core.annotation.SequencingPolicy`. A path like `org.axonframework.messaging.core.sequencing.annotation.SequencingPolicy` does not exist in the AF5 jar and causes a compile error. This is not obvious from the annotation's name — always verify with grep before committing.
- **`initialToken` migrates to `PooledStreamingEventProcessorConfiguration#initialToken(Function<TrackingTokenSource, CompletableFuture<TrackingToken>>)`.** AF4's `.initialToken(StreamableMessageSource::createHeadToken)` migrates to `.customized(config -> config.initialToken(source -> source.latestToken(null)))`. The AF5 **default** is a full replay from the start of the stream (`firstToken`) — so dropping the call without adding the AF5 equivalent causes a full historical replay. Preserve head-token semantics explicitly: `source -> source.latestToken(null)`.
- **`resetTokens(Function<...>)` lambda type changed.** AF4: `Function<StreamableMessageSource<TrackedEventMessage<?>>, TrackingToken>` (sync). AF5: `Function<TrackingTokenSource, CompletableFuture<TrackingToken>>` (async). Update any method reference like `StreamableMessageSource::createHeadToken` to a lambda: `source -> source.latestToken(null)`.

## Result

Inherits DEFAULT.md baseline. Recipe-specific augmentations per outcome:

### Success

Say **"return SUCCESS"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-event-processor`. NOTES per DEFAULT.md baseline (Success Criteria passed, retries used, idempotent / edits=none when applicable). Add a LEARNINGS bullet listing any flagged constructs the recipe did NOT migrate but the caller should know about — DLQ presence, `@EventHandlerInterceptor` placement, orphaned `@Bean SequencingPolicy`.

### Blocker

Say **"return BLOCKER"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-event-processor`. The recipe emits **one** Blocker result aggregating every detected blocker (see § Blocker, "Emission model — all blockers at once"). NOTES enumerate each detected blocker with its file:line. Options block has one sub-section per detected blocker — each with the three DEFAULT.md baselines (skip / revert / solve-manually).

Example (B1 — MongoTokenStore):

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.example.projector.MyProjector`
> **Recipe:** axon4to5-event-processor
>
> **Notes:** 1 blocker detected. Caller must resolve before re-invoking.
>
> 1. **B1 (MongoTokenStore)** at `AxonConfig.java:42` and `application.yaml:18` — `axon.eventhandling.processors.my-projector.token-store: mongo` plus `@Bean MongoTokenStore` definition. No AF5 release of the `axon-mongo` extension. AF4 Mongo data is not readable by AF5 `JpaTokenStore`; switching the store either replays from the event store or requires manual data migration.
>
> **Options:**
>
> _For B1 (MongoTokenStore):_
> - [ ] **skip** — keep `MyProjector` in its current partial state; queue moves on.
> - [ ] **revert** — undo this recipe's edits; restore the pre-recipe shape.
> - [ ] **solve-manually** — pause; caller switches to `JpaTokenStore` (replay from event store) and re-invokes.
```

### Rejected

Say **"return REJECTED"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-event-processor`. NOTES must name the failed `# Applicable` predicate (1 saga / 2 aggregate / 6 unrecognised) and, when a sister recipe handles the source, mention it.

Example:

```
return REJECTED

> **Result:** ⏭️ Rejected
> **Source:** `com.dddheroes.heroesofddd.creaturerecruitment.write.Dwelling`
> **Recipe:** axon4to5-event-processor
>
> **Notes:** Applicable predicate 2 failed — class is annotated `@Aggregate` with `@EventSourcingHandler` methods; this is an event-sourced aggregate, not an event-processor. Route to the aggregate recipe.
```

### Failure

Say **"return FAILURE"**, then **MUST emit** the result block (schema: FLOW.md § Result). NOTES must list failing Success Criteria + the last error verbatim. LEARNINGS nearly always present — record the hypothesis the next iteration starts from. Common Failure shape for this recipe: AF5 `Message` interface is non-generic (`CompletableFuture<? extends Message<?>>` does not compile); rewrite to `CompletableFuture<? extends Message>` and re-Apply.
