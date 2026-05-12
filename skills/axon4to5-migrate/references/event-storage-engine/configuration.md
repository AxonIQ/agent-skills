# Event-store / generic configuration class migration

Atomic migration of ONE class that touches AF4 `Configuration` / `Configurer` for one of the following bootstrap-level concerns:

- **Reads** — looks up `EventStore` / `EventBus` from `Configuration#eventStore()` / `eventBus()`.
- **Generic writes** — `@Bean ConfigurerModule` registering non-Axon components, `DefaultConfigurer.defaultConfiguration()` bootstrap entry point, free-standing `onStart` / `onShutdown` lifecycle hooks, `implements Lifecycle` component, generic `configurer.registerComponent(...)` calls.

Used by the main `event-storage-engine` recipe as a sub-reference because the storage engine is the bootstrap-layer concern and the same `@Configuration` class that registers the engine often also hosts these generic concerns. Topic-specific write configuration (event-processor wiring, aggregate registration, the storage-engine bean itself) is owned by its topic's main recipe; this file only covers the bootstrap chrome around them.

## Canonical reference

- [../../docs/paths/configuration.adoc](../../docs/paths/configuration.adoc) — `MessagingConfigurer` / `ModellingConfigurer` / `EventSourcingConfigurer`, `ConfigurerModule` → `ConfigurationEnhancer`, `ComponentRegistry`, lifecycle.
- [../../docs/paths/index.adoc](../../docs/paths/index.adoc) §"Import and package changes" — `org.axonframework.config` → `org.axonframework.configuration`, `org.axonframework.lifecycle` → folded into `ComponentDefinition`.

## Goal

- **Reads:** `config.eventStore()` / `config.eventBus()` rewritten to AF5 root-scoped `axonConfig.getOptionalComponent(...)`.
- **Generic writes:**
  - `Configurer` / `DefaultConfigurer` → focused `ApplicationConfigurer` (`MessagingConfigurer` / `ModellingConfigurer` / `EventSourcingConfigurer`).
  - `ConfigurerModule` → `ConfigurationEnhancer` acting on a `ComponentRegistry`.
  - `Configurer.onStart` / `onShutdown` → `lifecycleRegistry(...)` (free-standing) or `ComponentDefinition.onStart` / `onShutdown` (component-tied).
  - `Lifecycle` interface → folded into `ComponentDefinition`.
  - Generic component registration → `componentRegistry(cr -> cr.registerComponent(...))` (factory's `config` arg is now AF5 read-only `Configuration`).

## In scope

- ONE class with reads (`eventStore()` / `eventBus()`) OR generic write APIs:
  - `@Bean ConfigurerModule` (Spring) registering generic components or lifecycle.
  - `@Bean Configurer` / `DefaultConfigurer.defaultConfiguration()` (non-Spring or manual entry point).
  - `configurer.registerComponent(MyService.class, config -> ...)` for non-Axon services.
  - `configurer.onStart(Phase, () -> ...)` / `configurer.onShutdown(...)`.
  - `implements org.axonframework.lifecycle.Lifecycle`.

## Out of scope

- **Topic-specific write configuration** — owned by the topic's own recipe:
  - Event-processor beans / properties / error handlers / sequencing policy → [../event-processor/event-processor.md](../event-processor/event-processor.md) Steps 10–11.
  - Event-processor read lookups (`eventProcessor`, `tokenStore`, `sequencedDeadLetterProcessor`, async lifecycle on processors) → [../event-processor/configuration-reads.md](../event-processor/configuration-reads.md).
  - `commandBus()` read lookup → [../command-gateway/configuration-reads.md](../command-gateway/configuration-reads.md).
  - `queryBus()` / `queryUpdateEmitter()` read lookups → [../query-gateway/configuration-reads.md](../query-gateway/configuration-reads.md).
  - Aggregate / entity registration → [../aggregate/aggregate.md](../aggregate/aggregate.md) Path B.
  - Event-store bean swap → [event-storage-engine.md](event-storage-engine.md).
- **DLQ wiring** — Axoniq commercial; belongs to a future `axon4-to-axoniq5-deadletter` recipe.
- Saga lookup (`sagaConfiguration(type)`) — sagas out of scope at INIT.

## FQN cheat sheet

### AF4 (remove)

| Element | FQN |
|---|---|
| `Configuration` | `org.axonframework.config.Configuration` |
| `Configurer` | `org.axonframework.config.Configurer` |
| `DefaultConfigurer` | `org.axonframework.config.DefaultConfigurer` |
| `ConfigurerModule` | `org.axonframework.config.ConfigurerModule` |
| `Lifecycle` | `org.axonframework.lifecycle.Lifecycle` |
| `EventStore` (AF4 loc.) | `org.axonframework.eventsourcing.eventstore.EventStore` |
| `EventBus` (AF4 loc.) | `org.axonframework.eventhandling.EventBus` |

### AF5 (add)

| Element | FQN |
|---|---|
| `AxonConfiguration` | `org.axonframework.common.configuration.AxonConfiguration` |
| `Configuration` (read-only) | `org.axonframework.common.configuration.Configuration` |
| `ApplicationConfigurer` | `org.axonframework.configuration.ApplicationConfigurer` |
| `ConfigurationEnhancer` | `org.axonframework.configuration.ConfigurationEnhancer` |
| `ComponentRegistry` | `org.axonframework.configuration.ComponentRegistry` |
| `ComponentDefinition` | `org.axonframework.configuration.ComponentDefinition` |
| `LifecycleRegistry` | `org.axonframework.configuration.LifecycleRegistry` |
| `Phase` | `org.axonframework.common.lifecycle.Phase` *(unchanged FQN in AF5)* |
| `MessagingConfigurer` | `org.axonframework.configuration.MessagingConfigurer` |
| `ModellingConfigurer` | `org.axonframework.modelling.configuration.ModellingConfigurer` |
| `EventSourcingConfigurer` | `org.axonframework.eventsourcing.configuration.EventSourcingConfigurer` |
| `EventStore` | `org.axonframework.eventsourcing.eventstore.EventStore` *(FQN unchanged; AF5 keeps the type)* |
| `EventSink` (publish-side) | `org.axonframework.messaging.eventhandling.EventSink` |

## Procedure

Determine which side(s) apply, then run the matching steps:
- **Read** side detected (`eventStore()` / `eventBus()` calls) → run Steps R.1–R.3.
- **Write** side detected (generic ConfigurerModule / Configurer / Lifecycle) → run Steps W.1–W.8.
- **Mixed class** → run both sets; commit once when both ends compile.

### R.1. Switch the injected bean type

- If class only reads → `Configuration` (`org.axonframework.common.configuration.Configuration`).
- If class also touches root lifecycle → `AxonConfiguration` (`org.axonframework.common.configuration.AxonConfiguration`).
- Rename field accordingly. Update constructor parameter.

### R.2. Rewrite AF4 root lookups → AF5

AF4 root lookups returned the bean directly. AF5's `getOptionalComponent(...)` returns `Optional<T>`:

| AF4 call | AF5 replacement |
|---|---|
| `config.eventStore()` | `axonConfig.getOptionalComponent(EventStore.class).orElseThrow()` |
| `config.eventBus()` | `axonConfig.getOptionalComponent(EventSink.class).orElseThrow()` *(name change — `EventSink` is AF5 publish-side)* |
| `config.findComponent(EventStore.class)` | `axonConfig.getOptionalComponent(EventStore.class)` |

Use `.orElseThrow(...)` if AF4 code assumed presence; otherwise propagate the `Optional`.

### R.3. Sweep imports

- Remove stale AF4 imports: `org.axonframework.config.*`, AF4-located `EventStore` / `EventBus`.
- Add the AF5 equivalents from the cheat sheet.

### W.1. Locate (write side) and pick the right `ApplicationConfigurer`

```bash
grep -rln --include='*.java' --include='*.kt' \
  -e 'org.axonframework.config.Configurer\b' \
  -e 'org.axonframework.config.ConfigurerModule' \
  -e 'org.axonframework.config.DefaultConfigurer' \
  -e 'org.axonframework.lifecycle.Lifecycle\b' \
  <target>/src
```

Skip files whose only AF4 reference is read-side (covered by Steps R.* and the sibling reads files). Skip files whose only AF4 write reference is event-processor wiring, aggregate registration, or the event-store bean — those have their own recipes.

Configurers form a delegation chain: `MessagingConfigurer` ⊂ `ModellingConfigurer` ⊂ `EventSourcingConfigurer`. Pick the highest layer the class touches:

| Class touches | Pick |
|---|---|
| Only messaging (command/event/query bus, message handlers) | `MessagingConfigurer.create()` |
| Adds entities / repositories | `ModellingConfigurer.create()` |
| Adds event sourcing (event store, snapshots, event-sourced entities) | `EventSourcingConfigurer.create()` |

Escape hatches: `configurer.modelling(...)`, `configurer.messaging(...)`, `configurer.componentRegistry(...)`, `configurer.lifecycleRegistry(...)`. Use them when the AF4 call applied to a different layer than the one picked.

### W.2. (Path A — Spring Boot) `@Bean ConfigurerModule` → `@Bean ConfigurationEnhancer`

Run when `inputs.wiring == "spring-boot"`. Skip on Path B.

Lambda parameter type changes from `Configurer` (read+write) → `ComponentRegistry` (write only).

```java
// AF4
@Bean
public ConfigurerModule myModule() {
    return configurer -> configurer.registerComponent(
            MyService.class,
            config -> new MyServiceImpl());
}

// AF5
@Bean
public ConfigurationEnhancer myEnhancer() {
    return registry -> registry.registerComponent(
            MyService.class,
            config -> new MyServiceImpl());
}
```

Notes:
- Rename method `*Module` → `*Enhancer` if no other bean references it by name.
- Factory's `config` arg is now AF5 read-only `Configuration`. AF4 calls (`config.eventStore()`, `config.commandBus()`, …) → `config.getComponent(EventStore.class)` / `config.getComponent(CommandBus.class)` (Step W.6 has the full table).
- AF4 `Configurer#configureCommandBus` / `configureEventStore` / `configureSerializer` are **not** on `ComponentRegistry`. They live on the focused `ApplicationConfigurer` — switch to a bean that customises the configurer (Step W.3) or use the dedicated registration methods in non-Spring code.

### W.3. (Path B — framework Configurer) Manual `Configurer` → focused `ApplicationConfigurer`

Run when `inputs.wiring == "framework-config"`. Skip on Path A.

```java
// AF4
Configurer configurer = DefaultConfigurer.defaultConfiguration();
configurer.registerComponent(MyService.class, c -> new MyServiceImpl());
Configuration configuration = configurer.buildConfiguration();
configuration.start();

// AF5
EventSourcingConfigurer configurer = EventSourcingConfigurer.create();
configurer.componentRegistry(registry -> registry.registerComponent(
        MyService.class, c -> new MyServiceImpl()));
AxonConfiguration configuration = configurer.build();
configuration.start();
```

- `buildConfiguration()` → `build()`. Return type `AxonConfiguration` (extends `Configuration`).
- Bus / store registration stays on the focused configurer: `registerCommandBus` / `registerQueryBus` / `registerEventSink` on `MessagingConfigurer`; `registerEventStore` on `EventSourcingConfigurer`. Generic components flow through `componentRegistry(cr -> cr.registerComponent(...))`.

### W.4. Lifecycle handlers

AF4 had three places to hook lifecycle:
1. `Configurer.onStart(Phase, Runnable)` / `Configurer.onShutdown(Phase, Runnable)`.
2. Component implementing `Lifecycle` and overriding `registerLifecycleHandlers(LifecycleRegistry)`.
3. `@StartHandler` / `@ShutdownHandler` annotations on framework components.

AF5: lifecycle hooks attach to **two** places — the `LifecycleRegistry` for free-standing hooks, and a `ComponentDefinition` for hooks tied to a specific component.

#### Free-standing `onStart` / `onShutdown`

```java
// AF4
configurer.onStart(Phase.LOCAL_MESSAGE_HANDLER_REGISTRATIONS, () -> {
    // startup
    return CompletableFuture.completedFuture(null);
});

// AF5
configurer.lifecycleRegistry(lr -> lr.onStart(
        Phase.LOCAL_MESSAGE_HANDLER_REGISTRATIONS,
        config -> {
            // startup — config is AF5 Configuration
            return CompletableFuture.completedFuture(null);
        }));
```

Lambda now takes AF5 `Configuration` so the hook can read components without capturing them at registration time. Update the lambda signature and any references inside.

`Phase` constants keep their AF4 FQN (`org.axonframework.common.lifecycle.Phase`) — no import change.

#### Component-tied lifecycle (replacing `Lifecycle` interface)

AF4 `Lifecycle` interface is **removed**. Move both start and shutdown hooks into the `ComponentDefinition` registration:

```java
// AF4
class MyComponent implements Lifecycle {
    @Override
    public void registerLifecycleHandlers(@NotNull Lifecycle.LifecycleRegistry lifecycle) {
        lifecycle.onStart(Phase.LOCAL_MESSAGE_HANDLER_REGISTRATIONS, () -> {});
        lifecycle.onShutdown(Phase.LOCAL_MESSAGE_HANDLER_REGISTRATIONS, () -> {});
    }
}

// AF5 — registration owns the lifecycle
configurer.componentRegistry(cr -> cr.registerComponent(
        ComponentDefinition.ofType(MyComponent.class)
                           .withBuilder(config -> new MyComponent())
                           .onStart(Phase.LOCAL_MESSAGE_HANDLER_REGISTRATIONS, config -> {})
                           .onShutdown(Phase.LOCAL_MESSAGE_HANDLER_REGISTRATIONS, config -> {})));
```

Steps:
1. Remove `implements Lifecycle` and the `registerLifecycleHandlers` override from the component class.
2. Remove the AF4 import `org.axonframework.lifecycle.Lifecycle`.
3. Find the registration site — convert plain `(Type, factory)` → `ComponentDefinition` with hooks attached.
4. If registration lives in a *different* class, **flag** for the user — atomic scope is one class per run.

### W.5. Generic component registration

```java
// AF4
configurer.registerComponent(MyService.class, config -> new MyService());

// AF5 — generic
configurer.componentRegistry(cr -> cr.registerComponent(
        MyService.class,
        config -> new MyService()));

// AF5 — conditional
configurer.componentRegistry(cr -> cr.registerIfNotPresent(
        MyService.class,
        config -> new MyService()));

// AF5 — richer (lifecycle, decorators) — see ComponentDefinition above
```

When AF4 registered the same type *multiple* times under different *names*, use `cr.registerComponent(Type, name, factory)` (3-arg overload). AF5 `getComponents(Type)` returns `Map<String, T>` keyed by name.

### W.6. Reading inside the registration factory

Factories given to `registerComponent(Type, factory)` receive AF5 read-only `Configuration` as their argument. Rewrite AF4 read calls inside:

| AF4 factory call | AF5 factory call |
|---|---|
| `config.eventStore()` | `config.getComponent(EventStore.class)` |
| `config.commandBus()` | `config.getComponent(CommandBus.class)` |
| `config.queryBus()` | `config.getComponent(QueryBus.class)` |
| `config.eventBus()` | `config.getComponent(EventSink.class)` *(name change — `EventSink` is AF5 publish-side)* |
| `config.parameterResolverFactory()` | `config.getComponent(ParameterResolverFactory.class)` |
| custom `config.findComponent(Type)` | `config.getOptionalComponent(Type.class)` |

Apply **only** for factories *defined inside* this class. Read-only consumers in other classes are migrated by the per-topic reads files.

### W.7. DLQ sites — flag and leave alone

If the class calls `registerDeadLetterQueue(...)`, `registerDeadLetterQueueProvider(...)`, `registerEnqueuePolicy(...)`, or imports `JpaSequencedDeadLetterQueue` / `MongoSequencedDeadLetterQueue` / `SequencedDeadLetterQueueProviderConfigurerModule`:

- **Do not migrate.** DLQ is Axoniq commercial (`io.axoniq.framework:axoniq-dead-letter`) and belongs to a future `axon4-to-axoniq5-deadletter` recipe.
- Leave the AF4 DLQ code **as-is** in this class. It will not compile against AF5 free until the dedicated recipe runs — that is acceptable mid-migration.
- List every DLQ site in Output `notes`.

### W.8. Cleanup

After rewrite, remove from this class:
- Stale AF4 imports (`org.axonframework.config.*`, `org.axonframework.lifecycle.Lifecycle`, AF4 `TrackingEventProcessorConfiguration`).
- Now-unused private helper methods (factory lambdas inlined into `registerComponent`, helper builders).
- `implements Lifecycle` clauses on classes whose lifecycle hooks moved to `ComponentDefinition`.
- `@Bean ConfigurerModule` methods that became empty after per-topic extraction (event-processor, aggregate, event-store recipes already pulled those beans) — delete the bean entirely.

### W.9. Bootstrap-layer beans whose AF5 successor is missing or deferred

Some AF4 framework beans declared at application-bootstrap level (typically on `@SpringBootApplication` / a `@Configuration` class, outside any handler / aggregate / projector) have **no AF5 successor yet**. The most common case is `@Bean DeadlineManager` (see [../aggregate/not-supported.md](../aggregate/not-supported.md) B5 — `DeadlineManager`, `@DeadlineHandler`, `SimpleDeadlineManager`, `JobRunrDeadlineManager`, `QuartzDeadlineManager`, `DbSchedulerDeadlineManager` are gone). The same disposition applies wherever the bean's AF5 path is pinned as `accept-stays-af4` / `pause-migration` by a `not-supported.md` blocker.

**Disposition — comment out, never silently delete:**

```java
// TODO[AF5 migration]: DeadlineManager has no AF5 successor as of <version>.
//                      See aggregate/not-supported.md B5. Pinned decision:
//                      <blocker-key> = <user-choice> (progress.md).
//                      Restore this bean (or its replacement) once AF5 ships
//                      the deadline replacement / workflow API.
// @Bean
// public DeadlineManager deadlineManager(Configuration configuration) {
//     return SimpleDeadlineManager.builder()
//             .scopeAwareProvider(configuration.scopeAwareProvider())
//             .build();
// }
```

Rules:
1. The bean body MUST be commented out, not deleted — comment block preserves the AF4 wiring shape (factory, dependencies, builder calls) for the day the AF5 successor lands.
2. The `TODO[AF5 migration]` marker MUST cite the `not-supported.md` blocker key (e.g. `B5`) so a grep finds every parked bean from one place.
3. The blocker decision recorded at INIT (e.g. `deadline-handler: accept-stays-af4`) is the authoritative pin. If progress.md does NOT yet contain a relevant key, surface the bean to the user via `AskUserQuestion` BEFORE commenting it out, and record the resulting key.
4. Drop AF4-only `@EntityScan` entries (e.g. `SagaEntry.class`) that exist only to back the commented-out bean — `@EntityScan` is JPA wiring, not framework configuration, and a stale class reference on it is a compile error rather than a missing-feature signal. Note the drop alongside the TODO.
5. Stale AF4 imports that only the commented-out bean referenced are dropped per W.8.

Out of scope here: rewriting interceptor registrations whose AF4 → AF5 path exists (covered by the canonical doc — see [../../docs/paths/interceptors.adoc](../../docs/paths/interceptors.adoc)). This sub-step covers ONLY beans gated by an unresolved blocker.

## Verify

Invoke the external `axon4to5-isolatedtest` skill (see [../verification.md](../verification.md)):

```
Skill: axon4to5-isolatedtest
Inputs:
  target-name: <ClassSimpleName>
  build-file: <target>/pom.xml | <target>/build.gradle(.kts)
  main-sources:
    - src/main/java/<…>/<ConfigClass>.java
  test-sources:
    - src/test/java/<…>/<ConfigClass>IT.java    # omit (pass []) if no test class
  extra-deps:
    - org.axonframework:axon-configuration:${axon5.version}
    # plus any concrete AF5 deps the configuration writes against
  cleanup: false
```

Configuration writers usually need an integration test to verify behaviour, not just compilation. If none exists, flag for the user as a follow-up.
