# Recipe: event-processor (projector / handler component)

Atomic migration of ONE class with `@EventHandler` methods.

> If the candidate is a Spring `@Component` that **reads** `EventProcessingConfiguration` (rather than declaring `@EventHandler`), use [config-reads.md](config-reads.md) instead.

## Inputs

```yaml
target: <FQ class>                                          # required
target_test: <FQ test class>                                # optional; defaults to <target>Test
wiring: spring-boot | framework-config                       # pinned project decision
decisions: { ... }                                           # see ## Decision points
```

## Preflight

1. For each entry in `## Decision points` with `trigger: detected-at-preflight`, run its Detection. If it fires AND the key isn't in `inputs.decisions` → **🔒 await decision** for that key.
2. Sweep external configuration tied to this processor (the AF4 `@ProcessingGroup` name + paths below). The sweep populates context for later Procedure steps AND triggers Decision points for the blocker keys.
3. Idempotency: `mcp__ide__getDiagnostics` / `axon4to5-isolatedtest` (`test-sources: []`); if clean + tests green → **🔒 await decision** [`skip-or-deep-verify`](#skip-or-deep-verify).

### Configuration sweep targets

Grep for the AF4 `@ProcessingGroup("…")` name across the repo:

- Spring YAML/properties (Path A only): `axon.eventhandling.processors.<group>.*`.
- Java/Kotlin config (both paths): `registerSequencingPolicy`, `registerListenerInvocationErrorHandler`, `registerErrorHandler`, `registerDeadLetterQueue*`, `registerEnqueuePolicy`, `registerTokenStore`, `MongoTokenStore`, `org.axonframework.extensions.{mongo,kafka}`, `KafkaPublisher`, `StreamableKafkaMessageSource`, `KafkaMessageSourceConfigurer`.

Where each finding routes:

| Finding | Routes to |
|---|---|
| `sequencing-policy` / `registerSequencingPolicy` / `@Bean SequencingPolicy` | Step 7 (annotate class + delete AF4 source inline) |
| `registerListenerInvocationErrorHandler` / `registerErrorHandler` / `@Bean ListenerInvocationErrorHandler` | Step 11 (fold into `.customized(...errorHandler...)`) |
| `registerPooledStreaming…` / `registerSubscribing…` / `assignHandlerTypesMatching` | Step 10 (Spring `@Bean EventProcessorDefinition` / `eventProcessing(...)` chain) |
| DLQ wiring (`registerDeadLetterQueue*` / `axon…dlq.*` / `@Bean SequencedDeadLetterQueue`) | **OUT OF SCOPE** — Axoniq commercial recipe; leave AF4 wiring; record in `output.notes` as `dlq-sites-flagged` |
| `MongoTokenStore` / `registerTokenStore(MongoTokenStore…)` | Decision point [`mongo-token-store`](#mongo-token-store) (B5) |
| `org.axonframework.extensions.kafka.*` | Decision point [`axon-kafka`](#axon-kafka) (B7) |
| `@SagaEventHandler` / `@StartSaga` / `@EndSaga` / `@Saga` on the class | Decision point [`saga-handler-detected`](#saga-handler-detected) (B6) |

If nothing found → AF5 defaults apply; Step 7 is a no-op.

## Decision points

### mongo-token-store

- **Trigger**: detected-at-preflight (during config sweep)
- **Detection**:
    ```
    grep -RnE 'MongoTokenStore|registerTokenStore.*Mongo|org\.axonframework\.extensions\.mongo' --include='*.java' --include='*.kt' --include='*.yml' --include='*.yaml' --include='*.properties' <project root>
    ```
- **Question**: > "Project uses `MongoTokenStore` (no AF5 release of `axon-mongo`). Token data can be rebuilt by replay from the event store, but this is a deliberate user decision. How to handle?"
- **Options**:
    - `move-to-jpa-token-store` — code rewrite to AF5 `JpaTokenStore`; user runs replay from event store
    - `pause-migration` — user replaces token store (incl. data plan) before resuming
    - `accept-stays-af4` — keep token-store slice on AF4 deps; recipe exits
- **Auto-policy**:
    - `fallback: ask-user`
- **Effect**:
    - `move-to-jpa-token-store` → proceed; surface for `event-storage-engine` to replace the bean. `output.notes` notes "user accepts replay-from-event-store as the token-data plan".
    - `pause-migration` / `accept-stays-af4` → `output { result: blocked, reason: "mongo-token-store deferred — see blockers.md#B5" }`, exit.
- **Reference**: [blockers.md#B5](blockers.md#B5).

### saga-handler-detected

- **Trigger**: detected-at-preflight
- **Detection**:
    ```
    grep -RlnE '@SagaEventHandler\b|@StartSaga\b|@EndSaga\b|@Saga\b' --include='*.java' --include='*.kt' <candidate>
    ```
- **Question**: > "Candidate has saga annotations — this is a saga, not an event-processor. Route to saga recipe?"
- **Options**:
    - `wrong-recipe-skip` *(Recommended)* — orchestrator re-routes this candidate to the `saga` slot; this recipe exits untouched
    - `pause-migration` — user removes saga first
- **Auto-policy**:
    - `always: wrong-recipe-skip`
    - `fallback: ask-user`
- **Effect**:
    - `wrong-recipe-skip` → `output { result: rejected, route_to: saga, reason: "saga handlers detected" }`, exit. No edits.
    - `pause-migration` → `output { result: blocked }`, exit.
- **Reference**: [blockers.md#B6](blockers.md#B6).

### axon-kafka

- **Trigger**: detected-at-preflight (during config sweep)
- **Detection**:
    ```
    grep -RnE 'org\.axonframework\.extensions\.kafka|axon-kafka|KafkaPublisher|StreamableKafkaMessageSource|KafkaMessageSourceConfigurer' --include='*.java' --include='*.kt' --include='*.yml' --include='*.yaml' --include='*.properties' --include='pom.xml' --include='*.gradle*' <project>
    ```
- **Question**: > "Project uses `axon-kafka` (no AF5 release). KafkaPublisher / StreamableKafkaMessageSource / KafkaMessageSourceConfigurer reference AF4-only APIs. How to handle?"
- **Options**:
    - `accept-stays-af4` — Kafka slice stays AF4; affected modules won't compile against AF5
    - `pause-migration` — user replaces Kafka integration (native Kafka client + custom `EventBus` adapter, or move publication to Axon Server)
    - `remove-feature-first` — user deletes Kafka wiring now; re-introduces non-Axon Kafka later
- **Auto-policy**:
    - `fallback: ask-user`
- **Effect**:
    - any non-`none` choice → `output { result: blocked, reason: "axon-kafka deferred — see blockers.md#B7" }`, exit. No edits. `output.notes` records "user accepts axon-kafka has no AF5 path; Kafka slice is user's responsibility, out-of-band".
- **Reference**: [blockers.md#B7](blockers.md#B7).

### skip-or-deep-verify

- **Trigger**: triggered-in-procedure (only when Preflight idempotency check finds clean compile + green tests)
- **Question**: > "Target appears already migrated. Skip or deep-verify against AF4 baseline?"
- **Options**:
    - `skip` *(Recommended)* — `output { result: skipped }`
    - `deep-verify` — diff vs AF4 baseline; continue to Procedure if any silent loss detected
- **Auto-policy**:
    - `pinned.resolver_mode == "automatic": skip`
    - `fallback: ask-user`
- **Effect**:
    - `skip` → `output { result: skipped }`, exit.
    - `deep-verify` → continue to Procedure.

## Procedure

### Step 1 — Locate

User-named target, else first file matching `@ProcessingGroup` or AF4 `@EventHandler` AND one of: `CommandGateway` field / AF4 `@DisallowReplay` / AF4 `@MetaDataValue`.

### Step 2 — Confirm sweep results

Preflight already populated the sweep context. If `decisions.mongo-token-store`, `decisions.axon-kafka`, or `decisions.saga-handler-detected` are unresolved → re-emit the corresponding await (defensive; Preflight should have caught it).

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
4. Update import to AF5 `CommandDispatcher` (`org.axonframework.messaging.commandhandling.gateway.CommandDispatcher`).

If the gateway is used both in- and out-of-handler context, flag as **mixed class** in `output.notes` and schedule `command-gateway` as a follow-up pass.

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

If `commandDispatcher.send(cmd, helperOut)` doesn't compile because helper still returns AF4 `MetaData`, **flag** in `output.notes` as follow-up. Helper lives elsewhere; do NOT edit here. AF5 type: `org.axonframework.messaging.core.Metadata`.

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
- **`ListenerInvocationErrorHandler` impls are orphaned** — fold logic into the single `ErrorHandler` OR delete if it was a thin logging wrapper. **Flag** in `output.notes`; never silently drop.
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
   ```yaml
   target-name: <ProcessorSimpleName>
   main-sources: [<Processor>.java]
   test-sources: [<Processor>Test.java]    # [] if no tests
   extra-deps: [axon-messaging, axon-modelling, axon-test]
   ```

## Output

```yaml
result: success | skipped | rejected | blocked | failed
target: <FQ class>
reason: <one short line>
decisions:
  path: A (Spring Boot) | B (framework Configurer)
  processing-group: <name | "n/a">
  event-handler-mode: subscribing | tracking | "n/a"
  processor-definition-migrated: true | false
  error-handler-folded: none | propagating | custom | listener-invocation-orphaned
  dlq-sites-flagged: [<file:line>, …] | none
  mongo-token-store: none | move-to-jpa-token-store | pause-migration | accept-stays-af4
  saga-handler-detected: none | wrong-recipe-skip | pause-migration
  axon-kafka: none | accept-stays-af4 | pause-migration | remove-feature-first
files_touched:
  - <repo-relative path>
route_to: saga                                # only when saga-handler-detected = wrong-recipe-skip
notes: <free text — cite blockers.md#B<n> when blocked>
```

## Variants (Procedure shape, not decision points)

- **Pure projector (no command dispatch).** Steps 1–4 + 8–12 only. Skip 5–7. Return type stays `void`.
- **Saga-like with non-handler dispatch.** Class also exposes a public method dispatching outside `ProcessingContext`. Keep `CommandGateway` for that path AND add `CommandDispatcher` parameter on in-context handlers. Both coexist.
- **Mixed `@EventHandler` + `@QueryHandler`.** Out of scope here — surface in `output.notes`; orchestrator schedules `query-handler` afterwards.

## Subagent guidelines

```yaml
subagent_type: general-purpose
isolation: none
parallelism: per-item
on_unexpected_condition: keep-edits-and-fail
prompt-framing: |
  READ-ONLY analysis + edit of ONE event-processor target. Apply Steps 1–12 per ## Procedure
  using inputs.decisions (all blockers pre-resolved). Do NOT call AskUserQuestion.
```

**Eligibility**: subagent-eligible only AFTER `mongo-token-store`, `axon-kafka`, `saga-handler-detected`, `skip-or-deep-verify` are resolved (each is `fallback: ask-user` so main session must resolve interactively unless pinned).

## Anti-patterns

- Silent deletion of `registerPooledStreaming…` / `registerSubscribing…` / `assignHandlerTypesMatching` / `byDefaultAssignTo` — drops group name, segment count, batch size. Leave a `// TODO: confirm AF5 defaults match AF4 <name> settings` if defaults are genuinely intended.
- Deleting a `Configuration::eventStore` method reference inside such a registration — encodes which event source feeds the processor; carry it forward.

## Reference pairs (AF4 → AF5)

Bundled in [evals/fixtures/](../evals/fixtures/):

- **Projector + in-handler dispatch (`@ProcessingGroup` → `@Namespace`, `CommandGateway` → `CommandDispatcher`, `@SequencingPolicy` on class):** `axon4/heroes/WhenCreatureRecruitedThenAddToArmyProcessor.java` ↔ `axon5/heroes/WhenCreatureRecruitedThenAddToArmyProcessor.java`.
- **Pure projection (`@EventHandler` only, no command dispatch):** `axon4/heroes/DwellingReadModelProjector.java` ↔ `axon5/heroes/DwellingReadModelProjector.java`.
- **Spring `@Component` reading `EventProcessingConfiguration` (read-side variant — handled by [config-reads.md](config-reads.md)):** `axon4/heroes/StreamProcessorsOperations.java` ↔ `axon5/heroes/StreamProcessorsOperations.java`.
