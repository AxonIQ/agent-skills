# Recipe: event-processor (projector / handler component)

Atomic migration of ONE class with `@EventHandler` methods.

> If the candidate is a Spring `@Component` that **reads** `EventProcessingConfiguration` (rather than declaring `@EventHandler`), use [configuration-reads.md](config-reads.md) instead.

## Inputs

- `target` — FQ class (required)
- `target_test` — FQ test class (optional; auto `<target>Test`)
- `wiring` — `spring-boot` | `framework-config` (from pinned decisions)

## Preflight

1. Read [not-supported.md](blockers.md), run Detection greps. Resolve blockers before proceeding.
2. Same `mcp__ide__getDiagnostics` / `axon4to5-isolatedtest` pattern as other recipes — Skip/Deep-verify on green.

## Procedure

### Step 1 — Locate

Use user-named target, else first file matching `@ProcessingGroup` or AF4 `@EventHandler` AND one of: `CommandGateway` field / AF4 `@DisallowReplay` / AF4 `@MetaDataValue`.

### Step 2 — Sweep external configuration tied to this processor

Grep for the AF4 `@ProcessingGroup("…")` name across the repo:

- Spring YAML/properties (Path A only): `axon.eventhandling.processors.<group>.*`.
- Java/Kotlin config (both paths): `registerSequencingPolicy`, `registerListenerInvocationErrorHandler`, `registerErrorHandler`, `registerDeadLetterQueue*`, `registerEnqueuePolicy`, `registerTokenStore`, `MongoTokenStore`, `org.axonframework.extensions.{mongo,kafka}`, `KafkaPublisher`, `StreamableKafkaMessageSource`, `KafkaMessageSourceConfigurer`.

Where each finding goes:

| Finding | Action |
|---|---|
| `sequencing-policy` / `registerSequencingPolicy` / `@Bean SequencingPolicy` | Step 7 here — annotate class + delete AF4 source inline. |
| `registerListenerInvocationErrorHandler` / `registerErrorHandler` / `@Bean ListenerInvocationErrorHandler` | Step 11 — fold into `.customized(... errorHandler ...)`. |
| `registerPooledStreaming…` / `registerSubscribing…` / `assignHandlerTypesMatching` | Step 10 — `@Bean EventProcessorDefinition` (A) or `eventProcessing(…)` chain (B). |
| DLQ wiring (`registerDeadLetterQueue*` / `axon…dlq.*` / `@Bean SequencedDeadLetterQueue`) | **OUT OF SCOPE** — Axoniq commercial recipe. Leave AF4 wiring; flag in Output `notes`. NOT a blocker. |
| `MongoTokenStore` / `registerTokenStore(MongoTokenStore…)` | **Blocker B1** — JPA / pause / accept-stays-af4. |
| `org.axonframework.extensions.kafka.*` | **Blocker B3** — accept-stays-af4 / pause / remove-feature-first. |

If nothing found → AF5 defaults apply; skip Step 7.

### Step 3 — `@ProcessingGroup` → `@Namespace`

1:1 string. Update import to `org.axonframework.messaging.core.annotation.Namespace`.

**Binding rule.** The string in `@Namespace("<name>")` MUST equal every external reference (`axon.eventhandling.processors.<name>.*`, `pooledStreamingMatching("<name>")`, `processor("<name>", …)`). Mismatch = silent no-op (no events delivered).

If AF4 had no `@ProcessingGroup` but external config references the handler, still add `@Namespace` — AF5 does not auto-derive a group name from the package.

### Step 4 — Imports + sibling annotations

- `@EventHandler` → AF5 (`org.axonframework.messaging.eventhandling.annotation`).
- `@DisallowReplay` / `@ResetHandler` → `org.axonframework.messaging.eventhandling.replay.annotation`.
- `@MetaDataValue` → **`@MetadataValue`** (capital D). Package `org.axonframework.messaging.core.annotation`.
- Spring stereotypes (`@Component` etc.) untouched.
- Do NOT change handler-method visibility, name, or parameter order — AF5 resolves by type/annotation.

### Step 5 — Class-level `CommandGateway` → method-parameter `CommandDispatcher`

Rule from Javadoc: gateway = top-of-chain entry points; dispatcher = inside another handler. If the gateway is genuinely used outside any handler (public method, non-handler helper), keep it class-level and only update the import.

In-context steps:
1. Remove the `CommandGateway` field only.
2. Remove only the gateway parameter from the constructor — keep other params. Delete the constructor entirely if gateway was sole param (Path A → default ctor; Path B → registration lambda drops the arg).
3. Declare `CommandDispatcher commandDispatcher` as a method parameter on every in-context handler that dispatches commands:
   ```java
   @EventHandler
   public CompletableFuture<?> on(SomeEvent e, CommandDispatcher commandDispatcher) {
       return commandDispatcher.send(new MyCommand(e.id()));
   }
   ```
4. Update import to AF5 `CommandDispatcher`.

If the gateway is used both in- and out-of-handler context, flag as **mixed class** in Output notes and schedule `command-gateway` as a follow-up pass.

### Step 6 — Blocking `sendAndWait(…)` → async `send(…)`

`commandGateway.sendAndWait(cmd)` → `commandDispatcher.send(cmd)` (returns `CommandResult`).

Change handler return type `void` → `CompletableFuture<?>` whenever the body returns dispatcher result. **Framework consumes the future — never `.join()` / `.get()`.**

Shape preference:
1. **Single dispatch** → `return commandDispatcher.send(cmd, metadata);` (add `import java.util.concurrent.CompletableFuture;`).
2. **Loop / multiple dispatches** → `CompletableFuture.allOf(...)`:
   ```java
   var futures = items.stream()
       .map(it -> commandDispatcher.send(commandFor(it), metadata).getResultMessage())
       .toArray(CompletableFuture[]::new);
   return CompletableFuture.allOf(futures);
   ```
3. **Last resort — block with explicit timeout** (only when surrounding code can't go async):
   ```java
   commandDispatcher.send(cmd, metadata).getResultMessage().orTimeout(2, TimeUnit.SECONDS).join();
   ```

Branching rule: every branch must return a future. Use `CompletableFuture.completedFuture(null)` for no-op branches; invert `if (cond) dispatch;` to `if (!cond) return completedFuture(null); return dispatch;`.

`CommandResult` is NOT a `CompletableFuture`. To compose (`thenRun`, `allOf`, `orTimeout`) call `.getResultMessage()` first.

### Step 7 — `@SequencingPolicy` on the class (only if AF4 had explicit override)

AF5 default is `HierarchicalSequencingPolicy(SequentialPerAggregatePolicy → SequentialPolicy)` — identical to AF4's default. Skip if AF4 relied on default.

1. Annotate the class (or a single method — method-level wins over class-level):
   ```java
   @Namespace("...")
   @SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = "<metadataKey>")
   class MyProcessor { ... }
   ```
   `parameters` is `String[]`; `type` is `Class<? extends SequencingPolicy>` from `org.axonframework.messaging.core.sequencing.*`.
2. **Delete the AF4 source inline** so external config can't drift apart from the annotation:
   - YAML key `axon.eventhandling.processors.<group>.sequencing-policy`.
   - `@Bean SequencingPolicy<?>` (Path A) OR `EventProcessingConfigurer#registerSequencingPolicy(group, factory)` (both paths).
3. Custom `SequencingPolicy<EventMessage<?>>` impl — migrate:
   - Import `org.axonframework.eventhandling.async.SequencingPolicy` → `org.axonframework.messaging.core.sequencing.SequencingPolicy`.
   - `Object getSequenceIdentifierFor(EventMessage<?>)` → `Optional<Object> sequenceIdentifierFor(EventMessage<?>, ProcessingContext)`. Wrap return in `Optional.ofNullable(...)` if AF4 returned `null` for "no key".
   - `event.getPayload()` / `event.getMetaData()` → `event.payload()` / `event.metaData()`.

### Step 8 — Cleanup

After gateway removed: now-empty constructors / unused private fields / stale AF4 imports → delete.

### Step 9 — Helper-class metadata imports (out of scope)

If `commandDispatcher.send(cmd, helperOut)` doesn't compile because helper still returns AF4 `MetaData`, **flag** to user as follow-up. Helper lives elsewhere; do NOT edit here. AF5 type: `org.axonframework.messaging.core.Metadata`.

### Step 10 — Rewrite external configuration (per path)

Method-mapping cheat (both paths):

| AF4 (`EventProcessingConfigurer`) | AF5 |
|---|---|
| `registerPooledStreamingEventProcessor(name)` | `pooledStreaming(name).assigningHandlers(…).notCustomized()` |
| `registerPooledStreamingEventProcessor(name, source, customisation)` | `pooledStreaming(name).assigningHandlers(…).customized(config -> …)` |
| `registerSubscribingEventProcessor(name)` | `subscribing(name).assigningHandlers(…).notCustomized()` |
| `registerTrackingEventProcessor(name, …)` | **Removed.** Switch to `pooledStreaming(name)`. |
| `assignHandlerTypesMatching(group, predicate)` | merged into `assigningHandlers(EventHandlerSelector)` |
| `byDefaultAssignTo(group)` | use `pooledStreamingMatching(name)` (auto-selects by `@Namespace(name)`) OR an `EventHandlerSelector` matching everything not claimed by others |
| `registerSequencingPolicy(group, factory)` | **Delete** (handled by Step 7). |
| `registerErrorHandler(group, factory)` | fold into `.customized(config -> config.errorHandler(…))` (Step 11) |
| `registerListenerInvocationErrorHandler(group, factory)` | **Removed** — fold into the single `ErrorHandler` (Step 11) |
| `registerDeadLetterQueue*` / `registerEnqueuePolicy` | **OUT OF SCOPE** — Axoniq commercial recipe |

#### 10.A — Path A (Spring Boot)

AF4 `@Bean ConfigurerModule { configurer.eventProcessing()…}` → one `@Bean EventProcessorDefinition` **per processor**:

```java
@Bean
public EventProcessorDefinition myProcessorDefinition() {
    return EventProcessorDefinition.pooledStreaming("my-processor")
        .assigningHandlers(descriptor -> descriptor.beanType()
                .getPackageName().startsWith("com.my.projectors"))
        .customized(config -> config.initialSegmentCount(8).batchSize(100));
}
```

- `assigningHandlers` takes `EventHandlerSelector` (lambda on `BeanDescriptor` — `beanType()` / `beanName()`).
- Prefer `pooledStreamingMatching(name)` / `subscribingMatching(name)` when `@Namespace(name)` is set on handlers — drops `assigningHandlers(...)`.
- `.notCustomized()` for AF4 defaults; `.customized(config -> ...)` to set `initialSegmentCount`, `batchSize`, `maxClaimedSegments`, etc.
- Properties still bind to `EventProcessorSettings` under `axon.eventhandling.processors.<name>.*`. `mode: tracking` → `mode: pooled` (or `subscribing`). YAML entries containing only `sequencing-policy` can be deleted entirely (handled in Step 7).

#### 10.B — Path B (framework Configurer)

```java
PooledStreamingEventProcessorModule projectionProcessor = EventProcessorModule
    .pooledStreaming("<namespace>")
    .eventHandlingComponents(c -> c.autodetected(cfg -> new MyProjector(cfg.getComponent(MyRepo.class))))
    .notCustomized();

configurer.modelling(m -> m.messaging(msg ->
    msg.eventProcessing(ep -> ep.pooledStreaming(ps -> ps.processor(projectionProcessor)))));
```

`"<namespace>"` MUST equal `@Namespace("…")` on the handler class. `SubscribingEventProcessorModule` is the equivalent for subscribing processors.

For customisation: `.customized((cfg, conf) -> conf.batchSize(10).initialSegmentCount(8))`.

### Step 11 — Fold error handlers into `.customized(...)`

AF4 had TWO seams: `registerErrorHandler` (processor-level) + `registerListenerInvocationErrorHandler` (per-invocation). AF5 has ONE: `EventProcessorConfiguration.errorHandler(ErrorHandler)`. `ListenerInvocationErrorHandler` does NOT exist in AF5.

```java
@Bean
public EventProcessorDefinition myProcessorDefinition() {
    return EventProcessorDefinition.pooledStreaming("my-processor")
        .assigningHandlers(/* ... */)
        .customized(config -> config.errorHandler(myErrorHandler()));
}
```

FQNs:
- `ErrorHandler` — `org.axonframework.messaging.eventhandling.processing.errorhandling.ErrorHandler`
- `PropagatingErrorHandler` — `org.axonframework.messaging.eventhandling.processing.errorhandling.PropagatingErrorHandler`

Rules:
- `PropagatingErrorHandler.instance()` survives — re-import.
- Custom AF4 `ErrorHandler` impls need own signature migration.
- **`ListenerInvocationErrorHandler` impls are orphaned** — fold logic into the single `ErrorHandler` OR delete if it was a thin logging wrapper. **Flag** for the user; never silently drop.
- `registerDefaultErrorHandler(factory)` — apply resolved handler to every processor definition in this class; flag other config classes.
- Delete the AF4 `register*ErrorHandler` calls once `.errorHandler(...)` lands.

### Step 12 — Other class-internal cleanups

- `CommandExecutionException`: `org.axonframework.commandhandling` → `org.axonframework.messaging.commandhandling`. Update if present.
- `CommandCallback` SPI **removed** — rewrite to `CommandResult.onSuccess(…).onError(…)`:

  | AF4 | AF5 |
  |---|---|
  | `commandGateway.send(cmd, new CommandCallback<C,R>() { onResult(cmdMsg, resultMsg) { if (resultMsg.isExceptional()) ERR else OK } })` | `commandDispatcher.send(cmd).onSuccess(resultMsg -> { OK }).onError((resultMsg, throwable) -> { ERR });` |
  | `LoggingCallback.INSTANCE` / `NoOpCallback.INSTANCE` | drop the second arg: `commandDispatcher.send(cmd);` (framework logs failures by default) |

  Lambda param types: `onSuccess(Consumer<? super CommandResultMessage<?>>)`, `onError(BiConsumer<CommandResultMessage<?>, Throwable>)`. Read payload via `.payload()`, metadata via `.metaData()`.

  If AF4 callback was used to **block until completion** (e.g. `FutureCallback.getResult()`), use the Step 6 "block with explicit timeout" pattern instead.

## End condition

1. Zero compile errors in the class + its primary test class.
2. If test class exists, scoped tests pass via `axon4to5-isolatedtest` with:
   ```
   target-name: <ProcessorSimpleName>
   main-sources: [<Processor>.java]
   test-sources: [<Processor>Test.java]    # [] if no tests
   extra-deps: [axon-messaging, axon-modelling, axon-test]
   ```

## Output

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQ class>
reason: <one short line>
decisions:
  path: A (Spring Boot) | B (framework Configurer)
  processing-group: <name | "n/a">
  event-handler-mode: subscribing | tracking | "n/a"
  processor-definition-migrated: true | false                # Step 10
  error-handler-folded: none | propagating | custom | listener-invocation-orphaned   # Step 11
  dlq-sites-flagged: [<file:line>, …] | none                 # Step 2 sweep — surfaced
  mongo-token-store: none | move-to-jpa-token-store | pause-migration | accept-stays-af4   # B1
  saga-handler-detected: none | wrong-recipe-skip | pause-migration                          # B2
  axon-kafka: none | accept-stays-af4 | pause-migration | remove-feature-first              # B3
notes: <verbatim AskUserQuestion options for needs-decision>
```

`saga-handler-detected: wrong-recipe-skip` → `result: rejected` with `next: route-to:saga`.

## Variants

- **Pure projector (no command dispatch).** Steps 1–4 + 8–12 only. Skip 5–7. Return type stays `void`.
- **Saga-like with non-handler dispatch.** Class also exposes a public method dispatching outside `ProcessingContext`. Keep `CommandGateway` for that path AND add `CommandDispatcher` parameter on in-context handlers. Both coexist.
- **Mixed `@EventHandler` + `@QueryHandler`.** Out of scope here — surface in Output notes; orchestrator schedules `query-handler` afterwards.

## Anti-patterns

- Silent deletion of `registerPooledStreaming…` / `registerSubscribing…` / `assignHandlerTypesMatching` / `byDefaultAssignTo` — drops group name, segment count, batch size. Leave a `// TODO: confirm AF5 defaults match AF4 <name> settings` if defaults are genuinely intended.
- Deleting a `Configuration::eventStore` method reference inside such a registration — encodes which event source feeds the processor; carry it forward.

## Reference pairs (AF4 → AF5)

Bundled in [evals/fixtures/](../evals/fixtures/):

- **Projector + in-handler dispatch (`@ProcessingGroup` → `@Namespace`, `CommandGateway` → `CommandDispatcher`, `@SequencingPolicy` on class):** `axon4/heroes/WhenCreatureRecruitedThenAddToArmyProcessor.java` ↔ `axon5/heroes/WhenCreatureRecruitedThenAddToArmyProcessor.java`.
- **Pure projection (`@EventHandler` only, no command dispatch):** `axon4/heroes/DwellingReadModelProjector.java` ↔ `axon5/heroes/DwellingReadModelProjector.java`.
- **Spring `@Component` reading `EventProcessingConfiguration` (read-side variant — handled by [configuration-reads.md](config-reads.md)):** `axon4/heroes/StreamProcessorsOperations.java` ↔ `axon5/heroes/StreamProcessorsOperations.java`.
