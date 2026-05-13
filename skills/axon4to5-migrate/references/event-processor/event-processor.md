# Recipe: Event-handling component (EventProcessor / Projector / Saga-like reactor)

Atomic migration of ONE class with `@EventHandler` methods, typically `@ProcessingGroup`-annotated, optionally dispatching commands in response.

> **Read-side variant.** If the candidate class is a Spring `@Component` ops endpoint that *reads* `EventProcessingConfiguration` / `Configuration` to look up an event processor, token store, or DLQ processor (rather than declaring `@EventHandler` methods), follow [configuration-reads.md](configuration-reads.md) instead of this main recipe.

## Canonical reference

Read these for concepts, complete FQN moves and worked before/after examples — they are NOT repeated here.

- [../../docs/paths/projectors-event-processors.adoc](../../docs/paths/projectors-event-processors.adoc) — `@ProcessingGroup` → `@Namespace`, `PooledStreamingEventProcessor`, `QueryUpdateEmitter` as parameter, Spring vs non-Spring configuration, `EventProcessorDefinition` Spring bean shape, `EventProcessorSettings` binding.
- [../../docs/paths/sequencing-policies.adoc](../../docs/paths/sequencing-policies.adoc) — `@SequencingPolicy` annotation, AF4 → AF5 policy class moves.
- [../../docs/paths/dlq.adoc](../../docs/paths/dlq.adoc) — DLQ schema change, per-component scoping, no-MongoDB note (relevant to [not-supported.md](not-supported.md)).
- [../../docs/paths/interceptors.adoc](../../docs/paths/interceptors.adoc) — interceptor annotation moves (when present on the handler class).
- [../../docs/paths/configuration.adoc](../../docs/paths/configuration.adoc) — `MessagingConfigurer.eventProcessing(...)` chain, `EventProcessorModule` shape (relevant to Path B Step 10.B).
- [../../docs/paths/index.adoc](../../docs/paths/index.adoc) §"Import and package changes" — exhaustive FQN table.

This recipe holds only mechanical edits, scoped verify, and the blocker decision flow.

## Goal

The event-handling class compiles and behaves on AF5 APIs:
- `@ProcessingGroup` → `@Namespace`.
- `@EventHandler` import moves to AF5 location.
- Class-level `CommandGateway` field replaced with method-parameter `CommandDispatcher` bound to current `ProcessingContext`.
- Blocking `commandGateway.sendAndWait(...)` → async `commandDispatcher.send(...)` returning `CompletableFuture<?>`.
- `@DisallowReplay`, `@MetaDataValue` (capitalized to `@MetadataValue` in AF5) imports updated.

## Inputs

- target: FQ class name of the event-handling component (required)
- target_test: FQ test class name (optional — auto-discovered as `<target>Test` if absent)
- wiring: "spring-boot" | "framework-config" (required, supplied by migration runner from progress.md Pinned-decisions)

## End condition

1. Zero compile errors in the event-handling class and its primary test class.
2. If the projector has a test class, scoped tests pass.

## Output

Emit exactly one fenced ```yaml block per the six-variant Output contract
([../output-contract.md](../output-contract.md)). Schema below shows the
`success` shape with all event-processor `decisions` keys; for the other
five variants copy the matching example from `output-contract.md`.

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQ class>
reason: <one short line — required for every variant except success>
decisions:
  path: <A (Spring Boot) | B (framework Configurer)>     # taken from inputs.wiring
  processing-group: <name | "n/a">
  event-handler-mode: <subscribing | tracking | "n/a">
  processor-definition-migrated: <true | false>          # Step 10 — Spring @Bean or framework module rewrite
  error-handler-folded: <none | propagating | custom | listener-invocation-orphaned>   # Step 11
  dlq-sites-flagged: <list of file:line | "none">        # Step 2 sweep — out-of-scope, surfaced to user
  mongo-token-store: <none | move-to-jpa-token-store | pause-migration | accept-stays-af4>   # B1
  saga-handler-detected: <none | wrong-recipe-skip | pause-migration>                         # B2
  axon-kafka: <none | accept-stays-af4 | pause-migration | remove-feature-first>             # B3
caller-expects:
  commit: <true | false>
  next: <proceed | ask-user | record-and-skip | halt | route-to:<recipe>>
notes: <optional free text — verbatim AskUserQuestion options for needs-decision>
```

Blocker keys (`B1` / `B2` / `B3`) map to `result: blocked` or
`result: needs-decision` per [not-supported.md](not-supported.md).
`saga-handler-detected: wrong-recipe-skip` corresponds to `result: rejected`
with `caller-expects.next: route-to:saga`.

## Preflight

1. **Read [not-supported.md](not-supported.md) first** — run every Detection grep listed there against the candidate class and its processor-group config. If any blocker fires, follow that file's `AskUserQuestion` flow and apply its "Effect on Procedure" before doing anything else. Recipe must NOT proceed past Preflight while a blocker is unresolved.
2. Check compilation problems on the file. If zero AND the test class compiles too:
3. Run scoped tests if they exist.
4. If green AND no blocker fired → STOP. `AskUserQuestion`: Skip / Deep verify.
5. Only proceed if user picks **Deep verify** or step 2/3 reported failures.

## In scope

ONE class — Spring `@Component` (Path A) **or** a plain Java/Kotlin class registered via the framework `Configurer` (Path B) — that:
- Is annotated with `@ProcessingGroup("...")` (`org.axonframework.config.ProcessingGroup`), AND/OR
- Has at least one method annotated `@EventHandler` (`org.axonframework.eventhandling.EventHandler`).

Optionally:
- Injects `CommandGateway` (`org.axonframework.commandhandling.gateway.CommandGateway`) as constructor/field dependency.
- Calls `commandGateway.sendAndWait(...)` / `send(...)` inside `@EventHandler` methods.
- Uses `@MetaDataValue` (`org.axonframework.messaging.annotation.MetaDataValue`) on handler params.
- Annotated `@DisallowReplay` (`org.axonframework.eventhandling.DisallowReplay`).

## Out of scope

- Sagas (`@SagaEventHandler`, `@StartSaga`, `@EndSaga`) — currently not supported by this skill; the migration runner surfaces it at INIT.
- Top-of-chain `CommandGateway` callers (REST controllers etc. with NO `@EventHandler`) — those belong to the command-gateway recipe.

## FQN cheat sheet (recipe-specific quick lookup)

Full tables live in the canonical docs ([../../docs/paths/index.adoc](../../docs/paths/index.adoc), [../../docs/paths/projectors-event-processors.adoc](../../docs/paths/projectors-event-processors.adoc), [../../docs/paths/sequencing-policies.adoc](../../docs/paths/sequencing-policies.adoc)). Only the moves that change **how a single class is edited** are duplicated here:

| Element | AF4 → AF5 short form |
|---|---|
| `@ProcessingGroup` | *removed*; use `@Namespace("…")` (`org.axonframework.messaging.core.annotation`) |
| `@EventHandler` | package moves to `org.axonframework.messaging.eventhandling.annotation` |
| `@DisallowReplay` / `@ResetHandler` | package moves to `org.axonframework.messaging.eventhandling.replay.annotation` |
| `@MetaDataValue` | renamed to `@MetadataValue` (capital D), package `org.axonframework.messaging.core.annotation` |
| `CommandGateway` (top-of-chain only) | same name, package moves to `org.axonframework.messaging.commandhandling.gateway` |
| Inside-handler dispatch | NEW `CommandDispatcher` (`org.axonframework.messaging.commandhandling.gateway`) — method parameter |
| `@SequencingPolicy` (annotation, new in AF5) | `org.axonframework.messaging.core.annotation.SequencingPolicy` — see sequencing-policies doc for the policy-class table |

## Procedure

### 1. Locate the candidate

If user named target, use it. Otherwise:

```bash
grep -RlnE 'org\.axonframework\.config\.ProcessingGroup|org\.axonframework\.eventhandling\.EventHandler' \
     --include='*.java' --include='*.kt' <target>/src
```

Pick first lexical file that has BOTH `@EventHandler` method AND at least one of: `@ProcessingGroup`, `CommandGateway` field, AF4 `@DisallowReplay`, AF4 `@MetaDataValue` param.

### 2. Sweep for external configuration tied to this processor

Before transforming, grep for the AF4 processing-group name (string in `@ProcessingGroup("...")`). Sweep targets differ by `inputs.wiring`:

```bash
# Path A (Spring Boot) only — YAML / properties:
# typical keys: axon.eventhandling.processors.<group>.*, including …<group>.dlq.*
grep -rln --include='*.yml' --include='*.yaml' --include='*.properties' \
     '<group-name>' <project root>

# Both paths — Java/Kotlin config (@Bean for Path A, fluent Configurer chain for Path B)
grep -rln --include='*.java' --include='*.kt' \
     -e '<group-name>' \
     -e 'registerSequencingPolicy' \
     -e 'registerListenerInvocationErrorHandler' \
     -e 'registerErrorHandler' \
     -e 'registerDeadLetterQueue' \
     -e 'registerDeadLetterQueueProvider' \
     -e 'registerEnqueuePolicy' \
     -e 'SequencedDeadLetterQueue' \
     -e 'EnqueuePolicy' \
     -e 'registerTokenStore' \
     -e 'MongoTokenStore' \
     -e 'org\.axonframework\.extensions\.mongo' \
     -e 'org\.axonframework\.extensions\.kafka' \
     -e 'KafkaPublisher' \
     -e 'StreamableKafkaMessageSource' \
     -e 'KafkaMessageSourceConfigurer' \
     <source roots>
```

For Path B projects there is no `application.yml` — skip the YAML grep. The Java/Kotlin grep covers both `@Bean`-based wiring (Spring) and direct `EventProcessingConfigurer.registerX(...)` / `eventProcessing(ep -> ...)` calls in a plain `Configurer` setup.

What to do with the findings:

| Finding | Where it migrates |
|---|---|
| `axon.eventhandling.processors.<group>.sequencing-policy` / `registerSequencingPolicy` / custom `SequencingPolicy` `@Bean` | Step 7 here (annotate `@SequencingPolicy` on the class) AND delete the AF4 source inline (Step 7 sub-step 2) — no follow-up recipe |
| `registerListenerInvocationErrorHandler` / `registerErrorHandler` / `@Bean ListenerInvocationErrorHandler` | Step 11 here — fold into `.customized(builder -> builder.errorHandler(...))` |
| `registerPooledStreamingEventProcessor` / `registerSubscribingEventProcessor` / `assignHandlerTypesMatching` | Step 10 here — Spring `@Bean EventProcessorDefinition` (Path A) or programmatic `eventProcessing(...)` chain (Path B) |
| `axon.eventhandling.processors.<group>.dlq.*` / `registerDeadLetterQueue*` / `registerEnqueuePolicy` / `@Bean SequencedDeadLetterQueue` / `@Bean EnqueuePolicy` / `JpaSequencedDeadLetterQueue` / `MongoSequencedDeadLetterQueue` | **OUT OF SCOPE here.** DLQ is Axoniq commercial (`io.axoniq.framework:axoniq-dead-letter`) and belongs to a future `axon4-to-axoniq5-deadletter` recipe. Leave the AF4 DLQ wiring **untouched** in this run; flag every DLQ site in Output `notes`. NOT a blocker. |
| `MongoTokenStore` / `registerTokenStore(MongoTokenStore...)` / `org.axonframework.extensions.mongo.*` token-store imports | **Blocker B1 — see [not-supported.md](not-supported.md).** User picks JPA token store / pause / accept-stays-af4. |
| `KafkaPublisher` / `StreamableKafkaMessageSource` / `KafkaMessageSourceConfigurer` / `org.axonframework.extensions.kafka.*` | **Blocker B3 — see [not-supported.md](not-supported.md).** No AF5 release of `axon-kafka`. User picks accept-stays-af4 / pause / remove-feature-first. |

If sweep finds nothing → AF5 defaults apply, skip step 7.

### 3. Replace `@ProcessingGroup` → `@Namespace`

1:1 string argument. Update import.

**Binding rule.** The string in `@Namespace("<name>")` MUST equal every external reference to this processor — Spring keys (`axon.eventhandling.processors.<name>.*`), `pooledStreamingMatching("<name>")` / `subscribingMatching("<name>")` calls, programmatic registration. Mismatch compiles fine but produces a silent no-op (no events delivered). Match whatever the config side uses.

**AF4 had no `@ProcessingGroup` — still add `@Namespace` if external config references this handler.** Behaviour differs by path:
- **Path A (Spring Boot):** AF4 implicitly defaulted the group name to the handler's **package name** (Spring auto-discovery via `MessageHandlerLookup`). AF5 does NOT auto-derive — missing `@Namespace` means no namespace at all.
- **Path B (framework Configurer):** AF4 used whatever group name the explicit `EventProcessingConfigurer.assignHandlerTypesMatching(...)` / `registerEventHandler(...)` call used. AF5 is the same: the string in your `eventProcessing(ep -> ep.pooledStreaming(ps -> ps.processor("<name>", ...)))` call must match `@Namespace("<name>")`.

In both cases, if sweep (step 2) found a config-side reference (`axon.eventhandling.processors.<name>.*`, `pooledStreamingMatching("<name>")`, or `processor("<name>", ...)`), add `@Namespace("<name>")` using the same string.

### 4. Migrate `@EventHandler` import + sibling annotations

- `@EventHandler`: AF4 → AF5 location.
- `@DisallowReplay`: AF4 → AF5 location.
- `@ResetHandler`: AF4 → AF5 location (same package move as `@DisallowReplay`).
- `@MetaDataValue` → `@MetadataValue` (note capital D). Update both name and import.
- Keep framework-agnostic stereotypes (`@Component`, `@Service`, …) untouched.

**Do NOT change handler-method visibility, name, or parameter order.** AF5 resolves parameters by type/annotation, not position.

### 5. Replace class-level `CommandGateway` with method-parameter `CommandDispatcher`

In AF5, dispatching commands FROM a handler must use `CommandDispatcher` (gets the current `ProcessingContext` automatically). The class-level `CommandGateway` field is removed.

**Decision rule** (from `CommandDispatcher` Javadoc): gateway = top-of-chain entry points; dispatcher = inside another handler. If the gateway is genuinely used outside any handler (exposed publicly, called from a non-handler helper, used in a method without `ProcessingContext`), keep it as a class-level dependency and only update its import to the AF5 FQN.

Steps (in-context case):
1. Remove ONLY the `CommandGateway` field (e.g. `private final CommandGateway commandGateway;`). Other private fields on the class (calculators, repositories, helpers) stay untouched.
2. Remove ONLY the gateway parameter from the constructor — leave any other constructor parameters in place and keep their corresponding field assignments. Delete the entire constructor only when the gateway was its **sole** parameter; in Path A (Spring Boot) the default no-arg constructor is then used, and in Path B (framework Configurer) the registration site (e.g. `c -> new MyProjector()`) drops the gateway argument too.
3. For each `@EventHandler` (and any other in-context handler) that needs to send commands, declare `CommandDispatcher commandDispatcher` as a method parameter — auto-injected by `CommandDispatcherParameterResolverFactory`:
   ```java
   @EventHandler
   public CompletableFuture<?> on(SomeEvent e, CommandDispatcher commandDispatcher) {
       return commandDispatcher.send(new MyCommand(e.id()));
   }
   ```
4. Update the import to AF5 `CommandDispatcher` location.

If gateway is used outside handler methods too → **mixed class** — surface in Output notes so the migration runner schedules the command-gateway recipe as a follow-up pass.

### 6. Rewrite blocking `sendAndWait(...)` → async `send(...)`

| AF4 | AF5 |
|---|---|
| `commandGateway.sendAndWait(cmd)` | `commandDispatcher.send(cmd)` |
| `commandGateway.sendAndWait(cmd, metadata)` | `commandDispatcher.send(cmd, metadata)` |
| `commandGateway.send(cmd)` (fire-and-forget) | `commandDispatcher.send(cmd)` |
| `commandGateway.sendAndWait(cmd, ResultType.class)` | `commandDispatcher.send(cmd, ResultType.class)` (returns `CompletableFuture<ResultType>`) |

Change `@EventHandler` method return type `void` → `CompletableFuture<?>` whenever it now returns the dispatcher's result. Framework consumes the future — NO manual `.join()` / `.get()` / blocking.

**Dispatch shape — preference order:**

1. **Single dispatch → return the future directly.** `return commandDispatcher.send(cmd, metadata);` — framework consumes the result. Add `import java.util.concurrent.CompletableFuture;`.
2. **Loop / multiple dispatches → `CompletableFuture.allOf(...)`.** Collect each dispatch's `CompletableFuture<? extends Message>` (via `.getResultMessage()` on the `CommandResult`) into an array, return `CompletableFuture.allOf(futures)`.
   ```java
   var futures = items.stream()
       .map(it -> commandDispatcher.send(commandFor(it), metadata).getResultMessage())
       .toArray(CompletableFuture[]::new);
   return CompletableFuture.allOf(futures);
   ```
3. **Last resort — block with explicit timeout.** ONLY when the surrounding code cannot become async. Always `.getResultMessage().orTimeout(d, unit).join()` — never plain `.join()` / `.get()`:
   ```java
   commandDispatcher.send(cmd, metadata)
       .getResultMessage()
       .orTimeout(2, TimeUnit.SECONDS)
       .join();
   ```
   `CommandResult` is NOT a `CompletableFuture` — `.orTimeout(...)` lives on `CompletableFuture`, so `.getResultMessage()` is required first.

**Branching rules (when option 1 applies):**

- Every branch must return a future. Branches with no dispatch return `CompletableFuture.completedFuture(null)`.
- **Conditional dispatch — invert and early-return.** When AF4 was `if (cond) { commandGateway.sendAndWait(...); }` (no else, false branch is empty), invert and early-return for the no-op branch:
  ```java
  // PREFERRED
  if (!cond) {
      return CompletableFuture.completedFuture(null);
  }
  return commandDispatcher.send(cmd, metadata);
  ```
- Post-dispatch work (logging, bookkeeping) → chain with `.thenRun(...)` / `.thenApply(...)` on `commandResult.getResultMessage()`, NOT block.

**`CommandResult` vs `CompletableFuture`:** `commandDispatcher.send(...)` returns `CommandResult`, not `CompletableFuture`. Returning `CommandResult` directly from a `CompletableFuture<?>`-typed handler is fine — AF5's adapter accepts it. But to **compose** (`thenRun`, `allOf`, `orTimeout`, …), call `.getResultMessage()` first to get `CompletableFuture<? extends Message>`.

### 7. Sequencing policy — move from external config to `@SequencingPolicy` on the class

AF4: sequencing policy configured **outside** the class (Spring YAML `axon.eventhandling.processors.<group>.sequencing-policy`, or `@Bean`/`registerSequencingPolicy(group, factory)` in a config class). AF5: same policy *types* but attached directly to the handling component via `@SequencingPolicy`.

**Apply only when AF4 had an explicit override.** AF5 default is `HierarchicalSequencingPolicy(SequentialPerAggregatePolicy → SequentialPolicy)` — identical behaviour to AF4's default `SequentialPerAggregatePolicy` for aggregate-based event stores. If AF4 relied on the default, skip this step.

Detection (during step 2 sweep):
- YAML/properties: `axon.eventhandling.processors.<group>.sequencing-policy`.
- Java config: `EventProcessingConfigurer#registerSequencingPolicy(group, factory)` or a `@Bean SequencingPolicy<?>` wired by group name.
- Custom impl: a class implementing AF4 `org.axonframework.eventhandling.async.SequencingPolicy` — out of scope for this skill (separate signature change + package move).

AF4 → AF5 policy-class mapping table: [../../docs/paths/sequencing-policies.adoc](../../docs/paths/sequencing-policies.adoc). Custom impls are out of scope (separate signature change + package move).

Apply:

1. Annotate the event-processor class (or a single `@EventHandler` method when policy applies to one handler only — method-level wins over class-level):
   ```java
   @Namespace("...")
   @SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = "<metadataKey>")
   class MyProcessor { ... }
   ```
   - `parameters` is `String[]`. Single literal is fine; multiple → `parameters = {"a", "b"}`.
   - Compile-time `String` constants (e.g. `GameMetaData.GAME_ID_KEY`) work — annotation-legal.
   - `type` must be `Class<? extends SequencingPolicy>` from `org.axonframework.messaging.core.sequencing.*`.

2. **Delete the AF4 source inline** so the annotation and external config can't drift apart:
   - Remove the `axon.eventhandling.processors.<group>.sequencing-policy` key (and any sibling keys it nests under, if the YAML entry becomes empty).
   - Remove the `@Bean SequencingPolicy<?>` method that was group-wired by name (Path A) OR the `EventProcessingConfigurer#registerSequencingPolicy(group, factory)` call (Path A `@Bean ConfigurerModule` or Path B `eventProcessing(...)` chain). **Never** inline the policy into `EventProcessorDefinition.customized(...)` — that path does not exist in AF5.
   - Note the deletion in the diff summary so the user sees where the annotation landed.

3. **If AF4 had a custom `SequencingPolicy<EventMessage<?>>` impl, migrate the impl class.** The annotation on the processor is the same mechanical move; the impl class itself is a deterministic three-edit rewrite:

   | AF4 | AF5 |
   |---|---|
   | `import org.axonframework.eventhandling.async.SequencingPolicy;` | `import org.axonframework.messaging.core.sequencing.SequencingPolicy;` |
   | `class MyPolicy implements SequencingPolicy<EventMessage<?>>` | unchanged — same generic param works (`SequencingPolicy<M extends Message<?>>`). |
   | `Object getSequenceIdentifierFor(EventMessage<?> event)` | `Optional<Object> sequenceIdentifierFor(EventMessage<?> event, ProcessingContext context)` — rename method, add `ProcessingContext` param, wrap the AF4 return in `Optional.ofNullable(...)`. |
   | `event.getPayload()` / `event.getMetaData()` inside the impl | `event.payload()` / `event.metaData()` (record-style accessors, AF5-wide). |

   Imports to add: `import java.util.Optional;` and `import org.axonframework.messaging.unitofwork.ProcessingContext;`. Imports to drop: AF4 `org.axonframework.eventhandling.async.SequencingPolicy`.

   Annotate the processor class (Step 7 main flow above) with `@SequencingPolicy(type = MyPolicy.class)` pointing at the migrated impl FQN.

   If the AF4 impl returned `null` to mean "no sequencing key" (rare, but legal in AF4), translate via `Optional.ofNullable(...)`. If the AF4 impl returned a sentinel (`""` or `0L`), keep the sentinel — only `null` should become `Optional.empty()`.

### 8. Cleanup after gateway removal

After the gateway is gone, scan the class for:
- Now-empty constructors → delete (Path A: Spring uses default no-arg; Path B: registration lambda becomes `c -> new MyProjector()`) or leave as default.
- Now-unused private fields → delete.
- Stale imports (`CommandGateway`, AF4 `org.axonframework.*` packages) → delete.

### 9. Out-of-scope: helper-class metadata imports

A common project pattern: a helper like `XxxMetaData.with(...)` that returns the framework's metadata type. In AF5 that should be `org.axonframework.messaging.core.Metadata`. **The per-processor recipe does NOT migrate that helper** — it lives in another package and may be shared across many handlers. If `commandDispatcher.send(cmd, helperOut)` fails to compile because the helper still returns AF4 `org.axonframework.messaging.MetaData`, **flag it for the user** as a follow-up — do not edit the helper here.

### Path A — Spring Boot

Use when `inputs.wiring == "spring-boot"`. The class itself is fully migrated by Steps 1–9. Wiring-side details:

- Class stays a Spring stereotype (`@Component` / `@Service`) — `MessageHandlerLookup` auto-discovers `@EventHandler` methods at startup. No manual registration needed.
- Processor properties stay in `application.yml` under `axon.eventhandling.processors.<name>.*`. AF5 binds them to `EventProcessorSettings`. Several leaves were renamed/removed — see Step 10.A.YAML.
- Per-processor `@Bean ConfigurerModule` calling `configurer.eventProcessing()` → one `@Bean EventProcessorDefinition` per processor. See Step 10.A.

### Path B — framework Configurer

Use when `inputs.wiring == "framework-config"`. The class itself is fully migrated by Steps 1–9. Wiring-side details:

- The class is registered explicitly in the project's Configurer chain. **Canonical pattern** (AF5 5.x): build a `PooledStreamingEventProcessorModule` (or its `Subscribing` counterpart), then attach it to the configurer through the `modelling → messaging → eventProcessing` chain.

  AF4 typical:
  ```java
  configurer.eventProcessing()
      .registerEventHandler(c -> new MyProjector(repository));
  ```

  AF5 equivalent — annotation-based handler class (uses `@EventHandler` methods on `MyProjector`):
  ```java
  PooledStreamingEventProcessorModule projectionProcessor = EventProcessorModule
          .pooledStreaming("<namespace>")
          .eventHandlingComponents(c -> c.autodetected(
                  cfg -> new MyProjector(cfg.getComponent(MyRepository.class))))
          .notCustomized();

  configurer.modelling(modelling -> modelling.messaging(messaging ->
          messaging.eventProcessing(eventProcessing ->
                  eventProcessing.pooledStreaming(ps -> ps.processor(projectionProcessor)))));
  ```
  The `"<namespace>"` string MUST equal the value in `@Namespace("...")` on the handler class (Step 3 binding rule).

  AF5 equivalent — declarative `EventHandlingComponent` (no `@EventHandler`, explicit `subscribe(...)` calls; rare during 4→5 migration but legal):
  ```java
  PooledStreamingEventProcessorModule automationProcessor = EventProcessorModule
          .pooledStreaming("<namespace>")
          .eventHandlingComponents(c -> c.declarative(cfg ->
                  SimpleEventHandlingComponent.create("<component-name>")
                          .subscribe(new QualifiedName(SomeEvent.class), MyProjector::react)))
          .notCustomized();
  ```

- There is no `application.yml` to sweep. Processor configuration (batch size, segment count, error handler) is set programmatically via `.customized(...)`. See Step 10.B for the full mapping.

- `SubscribingEventProcessor` equivalent:
  ```java
  SubscribingEventProcessorModule notificationsProcessor = EventProcessorModule
          .subscribing("<namespace>")
          .eventHandlingComponents(c -> c.autodetected(cfg -> new NotificationHandler(...)))
          .notCustomized();

  configurer.modelling(modelling -> modelling.messaging(messaging ->
          messaging.eventProcessing(eventProcessing ->
                  eventProcessing.subscribing(sub -> sub.processor(notificationsProcessor)))));
  ```

### 10. Migrate this processor's external configuration

Rewrite the configuration sites that Step 2's sweep flagged for this processor (`registerPooledStreamingEventProcessor` / `registerSubscribingEventProcessor` / `assignHandlerTypesMatching` / `byDefaultAssignTo`, plus the YAML/properties keys). Pick the path:

- `inputs.wiring == "spring-boot"` → run Step 10.A.
- `inputs.wiring == "framework-config"` → run Step 10.B.

Method-mapping cheat sheet (shared across both paths):

| AF4 (on `EventProcessingConfigurer`) | AF5 (`EventProcessorDefinition` builder — Path A / `eventProcessing(...)` chain — Path B) |
|---|---|
| `registerPooledStreamingEventProcessor(name)` | `pooledStreaming(name).assigningHandlers(...).notCustomized()` |
| `registerPooledStreamingEventProcessor(name, source, customisation)` | `pooledStreaming(name).assigningHandlers(...).customized(config -> /* translate builder */)` |
| `registerSubscribingEventProcessor(name)` | `subscribing(name).assigningHandlers(...).notCustomized()` |
| `registerTrackingEventProcessor(name, ...)` | **Removed.** Switch to `pooledStreaming(name)`. |
| `assignHandlerTypesMatching(group, predicate)` | merged into `assigningHandlers(EventHandlerSelector)` on the processor |
| `byDefaultAssignTo(group)` | the receiving definition becomes the default sink — give it an `EventHandlerSelector` matching everything not claimed by others, OR use `pooledStreamingMatching(name)` (auto-selects by `@Namespace(name)`) |
| `registerSequencingPolicy(group, factory)` | **Delete.** Already handled by Step 7 sub-step 2. |
| `registerErrorHandler(group, factory)` | fold into the same processor's `.customized(config -> config.errorHandler(...))` — see Step 11 |
| `registerDefaultErrorHandler(factory)` | apply to **every** definition in this class — see Step 11 |
| `registerListenerInvocationErrorHandler(group, factory)` | **Removed.** Listener-invocation seam is gone; the per-processor `ErrorHandler` is the only seam now — see Step 11 |
| `registerDeadLetterQueue` / `registerDeadLetterQueueProvider` / `registerEnqueuePolicy` | **OUT OF SCOPE.** Flag in Output `notes` for `axon4-to-axoniq5-deadletter`. Do not migrate. |

FQN cheat sheet (Spring `@Bean` types added on Path A; framework configurers used by both paths):

| Element | FQN |
|---|---|
| `EventProcessorDefinition` (Spring) | `org.axonframework.extension.spring.config.EventProcessorDefinition` |
| `EventHandlerSelector` | `org.axonframework.extension.spring.config.EventHandlerSelector` |
| `EventProcessorSettings` | `org.axonframework.extension.spring.config.EventProcessorSettings` |
| `MessagingConfigurer` | `org.axonframework.configuration.MessagingConfigurer` |
| `EventProcessorModule` | (see Path B code above — re-imports `org.axonframework.messaging.eventhandling.processing.*`) |

#### 10.A. Path A — `EventProcessingConfigurer` → `@Bean EventProcessorDefinition`

AF4 typically had a `@Bean ConfigurerModule` that called `configurer.eventProcessing()` and chained per-processor registrations. AF5 expresses each processor as its **own** `@Bean EventProcessorDefinition`. **One bean per processor**, no shared lambda.

```java
// AF4
@Bean
public ConfigurerModule configure() {
    return configurer -> {
        EventProcessingConfigurer p = configurer.eventProcessing();
        p.registerPooledStreamingEventProcessor(
                "my-processor",
                org.axonframework.config.Configuration::eventStore,
                (config, builder) -> builder.initialSegmentCount(8).batchSize(100))
         .assignHandlerTypesMatching(
                "my-processor",
                type -> type.getPackageName().startsWith("com.my.projectors"));
    };
}

// AF5 — one bean per processor
@Bean
public EventProcessorDefinition myProcessorDefinition() {
    return EventProcessorDefinition
            .pooledStreaming("my-processor")
            .assigningHandlers(descriptor -> descriptor.beanType()
                    .getPackageName().startsWith("com.my.projectors"))
            .customized(config -> config.initialSegmentCount(8).batchSize(100));
}
```

Notes:
- `assigningHandlers` takes an `EventHandlerSelector` lambda; param is `BeanDescriptor` (`descriptor.beanType()`, `descriptor.beanName()`). Replaces *both* `assignHandlerTypesMatching` and `byDefaultAssignTo`.
- `pooledStreamingMatching(name)` / `subscribingMatching(name)` shortcut factories auto-select handlers by `@Namespace(name)`. If Step 3 already landed (handlers carry `@Namespace`) and processor-name matches, prefer `*Matching` — eliminates `assigningHandlers(...)` entirely.
- `.customized(...)` vs `.notCustomized()` — `notCustomized` when AF4 used defaults; `customized(config -> ...)` when AF4 customised the builder. AF5 config object exposes the same surface: `initialSegmentCount`, `batchSize`, `maxClaimedSegments`, etc.
- Properties-based config still works. AF5 binds `axon.eventhandling.processors.<name>.*` to `EventProcessorSettings`. `EventProcessorDefinition` beans coexist with properties; explicit `.customized(...)` overrides the properties.

##### 10.A.YAML. Properties / YAML adjustments

AF4 keys are scoped by **processing-group name**; AF5 keeps the same root key but scopes by **processor name** (after AF4's group/processor identity collapses, typically the same string). Several leaves were renamed/removed:
- `mode: tracking` is gone — use `mode: pooled` (default streaming) or `mode: subscribing`.
- `sequencing-policy` config moved to class-level `@SequencingPolicy` annotation (Step 7). When the only thing under a group key is `sequencing-policy`, the YAML entry can usually be **deleted** entirely.

#### 10.B. Path B — `EventProcessingConfigurer` → `MessagingConfigurer#eventProcessing(...)`

Configures event processing programmatically — no Spring beans involved:

```java
// AF4
configurer.eventProcessing()
          .registerPooledStreamingEventProcessor("my-processor");

// AF5
messagingConfigurer.eventProcessing(
    eventProcessing -> eventProcessing.pooledStreaming(
        pooledStreaming -> pooledStreaming.processor(
            "my-processor",
            module -> module.eventHandlingComponents(components -> components)
                            .notCustomized())));
```

If AF4 customised the builder (segments, batch size, …), translate into `.customized((cfg, conf) -> conf.batchSize(10).initialSegmentCount(8))` on the inner `EventProcessorModule` — see the Path B subsection above for the full handler-class registration shape.

### 11. Fold error handlers into `EventProcessorDefinition.customized(...)` / `EventProcessorModule.customized(...)`

AF4 had two seams per processing group: `registerErrorHandler` (processor-level — outer loop fails) and `registerListenerInvocationErrorHandler` (per `@EventHandler` invocation). AF5 collapses both into **one** seam: a single `ErrorHandler` per processor via `EventProcessorConfiguration.errorHandler(ErrorHandler)`. `ListenerInvocationErrorHandler` does **not exist** in AF5.

```java
// AF4
return configurer -> {
    EventProcessingConfigurer p = configurer.eventProcessing();
    p.registerErrorHandler("my-processor",
            config -> PropagatingErrorHandler.instance());
    p.registerListenerInvocationErrorHandler("my-processor",
            config -> new LoggingListenerInvocationErrorHandler());
};

// AF5 Path A — both fold into the same .customized(...)
@Bean
public EventProcessorDefinition myProcessorDefinition() {
    return EventProcessorDefinition.pooledStreaming("my-processor")
            .assigningHandlers(/* ... */)
            .customized(config -> config.errorHandler(myErrorHandler()));
}
```

FQN cheat sheet:

| Element | FQN |
|---|---|
| `ErrorHandler` (per-processor) | `org.axonframework.messaging.eventhandling.processing.errorhandling.ErrorHandler` |
| `PropagatingErrorHandler` | `org.axonframework.messaging.eventhandling.processing.errorhandling.PropagatingErrorHandler` |

Steps:

1. **Pick the AF5 `ErrorHandler`** for the AF4 setting:
   - `PropagatingErrorHandler.instance()` keeps name and behaviour — re-import from `org.axonframework.messaging.eventhandling.processing.errorhandling.PropagatingErrorHandler`.
   - Custom AF4 `ErrorHandler` impls need their own migration (signature changed); the **registration** rewrite here is mechanical.
   - **`ListenerInvocationErrorHandler` impls are orphaned.** No AF5 equivalent. Two options: (a) fold listener-invocation logic into the processor's single `ErrorHandler`; (b) delete if it was a thin logging wrapper now covered by AF5 default behaviour. **Flag** for the user — never silently drop a custom impl.
2. **Merge into the matching definition / module** — add `.errorHandler(...)` inside `.customized(config -> ...)`. If the definition/module was `.notCustomized()`, switch to `.customized(config -> config.errorHandler(...))`. Other customisations (segments, batch size, …) chain on the same `config`.
3. **`registerDefaultErrorHandler(factory)`** — AF5 has no default-only knob today. Apply the resolved `ErrorHandler` to **every** processor definition in this class. Flag any other configuration class in the project that defines processor definitions (separate run).
4. **Delete** AF4 `registerErrorHandler` / `registerListenerInvocationErrorHandler` / `registerDefaultErrorHandler` once `.errorHandler(...)` has landed.

### 12. Verify nothing else needs migrating in this class

- Try/catch on `CommandExecutionException`: FQN moved (`org.axonframework.commandhandling` → `org.axonframework.messaging.commandhandling`). Update if present.
- `CommandCallback` SPI removed — **rewrite to `CommandResult.onSuccess(...).onError(...)`** (mechanical):

  | AF4 shape | AF5 rewrite |
  |---|---|
  | `commandGateway.send(cmd, new CommandCallback<C, R>() { onResult(cmdMsg, resultMsg) { if (resultMsg.isExceptional()) {ERR} else {OK} } })` | `commandDispatcher.send(cmd).onSuccess(resultMsg -> { OK }).onError((resultMsg, throwable) -> { ERR });` |
  | older split: `new CommandCallback<C, R>() { onSuccess(cmdMsg, result, metadata) {OK}; onFailure(cmdMsg, cause) {ERR} }` | same — `.onSuccess(resultMsg -> { OK using resultMsg.payload() / resultMsg.metaData() }).onError((resultMsg, throwable) -> { ERR using throwable })` |
  | `LoggingCallback.INSTANCE` / `NoOpCallback.INSTANCE` (fire-and-forget logging) | drop the second arg entirely — `commandDispatcher.send(cmd);` (framework logs failures by default) |
  | Inside an `@EventHandler` body | use `commandDispatcher` per Step 5; chain `.onSuccess` / `.onError` on the returned `CommandResult` BEFORE returning, not after `.getResultMessage()` |

  Imports: drop `org.axonframework.commandhandling.callbacks.CommandCallback` (and `LoggingCallback` / `NoOpCallback` / `FutureCallback`). No AF5 import to add — `onSuccess` / `onError` live on `CommandResult` returned by `commandDispatcher.send(...)`.

  **`CommandResult` lambda parameter types.**
  - `onSuccess(Consumer<? super CommandResultMessage<?>>)` → lambda param is `CommandResultMessage<?>`. Read payload via `.payload()`, metadata via `.metaData()`.
  - `onError(BiConsumer<CommandResultMessage<?>, Throwable>)` → lambda gets both the (possibly null) result message and the throwable.

  **Caveats.**
  - If AF4 callback was used to **block until completion** (e.g. `FutureCallback` then `.getResult()`), this is no longer a callback — it's a sync wait. Use the "Last resort — block with explicit timeout" pattern from Step 6 (`.getResultMessage().orTimeout(d, unit).join()`) instead of trying to preserve the callback.
  - If the callback referenced a class field outside the handler scope (rare), keep the closure intact — lambdas capture by reference like inner classes.

## Verify (against End condition)

If surrounding code still uses AF4 APIs, scope verification to the projector via the external `axon4to5-isolatedtest` skill (see [../verification.md](../verification.md)):

```
Skill: axon4to5-isolatedtest
Inputs:
  target-name: <ProcessorSimpleName>            # e.g. WhenCreatureRecruitedThenAddToArmy
  build-file: <target>/pom.xml | <target>/build.gradle(.kts)
  main-sources:
    - src/main/java/<…>/<Processor>.java
  test-sources:
    - src/test/java/<…>/<Processor>Test.java    # omit if no test class
  extra-deps:
    - org.axonframework:axon-messaging:${axon5.version}
    - org.axonframework:axon-modelling:${axon5.version}
    - org.axonframework:axon-test:${axon5.version}        # only when test-sources present
  cleanup: false                                 # true on recipe's last successful run
```

If the projector has no test class, pass `test-sources: []`; the external skill runs the compile-only branch and reports `0 executed`. Still better to flag to user as a follow-up to add tests.

## Variants

- **Pure projector (no command dispatch).** Handler reads event + updates read model — no `CommandGateway`. Apply steps 1–4 + 8–12 only. Skip 5–7. Return type stays `void`.
- **Saga-like reactor with non-handler dispatch.** Class also exposes a public method that dispatches commands outside any `ProcessingContext` (REST endpoint, scheduler entry). Keep `CommandGateway` as a class-level dependency for that path AND add `CommandDispatcher` as a method parameter on in-context handlers. Both coexist.
- **Mixed `@EventHandler` + `@QueryHandler`.** `CommandDispatcher` parameter resolution applies to query handlers too — declare it as a method parameter wherever the handler runs inside a `ProcessingContext`. Out of scope here; surface in Output notes so the migration runner schedules the query-handler recipe afterwards.

## Anti-patterns

- **Never delete `registerPooledStreamingEventProcessor(...)`, `registerSubscribingEventProcessor(...)`, `assignHandlerTypesMatching(...)`, or `byDefaultAssignTo(...)` calls.** Step 10 owns the rewrite to `@Bean EventProcessorDefinition` (Path A) or the `eventProcessing(...)` chain (Path B). Silent deletion drops the group name, segment count, batch size, executor binding, and source selection — runtime semantics change without a diff trail and the misconfiguration only surfaces under load. If AF5 defaults are genuinely the intended target, leave a `// TODO: confirm AF5 defaults match AF4 <name> settings` comment next to the deletion so the reviewer can audit it instead of guessing.
- **Never delete a `Configuration::eventStore` method reference inside such a registration** — it encodes which event source feeds the processor. Carry it forward in the rewrite (see Step 10 cheat sheet).

## Examples

See [examples/](examples/) for real-world before/after migrations.
