# Query-bus configuration reads

Read-side migration for a class that **injects AF4 `Configuration` to look up `QueryBus` / `QueryUpdateEmitter`**. Rare — most projects inject `QueryGateway` / `QueryUpdateEmitter` directly. Use this when a Spring `@Component` / service reaches through `Configuration#queryBus()` to dispatch low-level query messages or emit subscription updates at runtime.

Used by the main `query-gateway` recipe as a sub-reference when the candidate is a configuration **reader**, not a top-of-chain `QueryGateway` caller.

## Canonical reference

- [../../docs/paths/configuration.adoc](../../docs/paths/configuration.adoc) — `Configurer` split, `AxonConfiguration` / `Configuration`, component lookup model.
- [../../docs/paths/index.adoc](../../docs/paths/index.adoc) §"Import and package changes" — `org.axonframework.config` → `org.axonframework.common.configuration`.

## Goal

- Injected bean changed from AF4 `Configuration` (`org.axonframework.config.Configuration`) to AF5 `Configuration` (`org.axonframework.common.configuration.Configuration`) — or `AxonConfiguration` when the class also touches root lifecycle.
- AF4 `config.queryBus()` / `config.queryUpdateEmitter()` rewritten to AF5 root-scoped lookup.

## FQN cheat sheet

| AF4 | AF5 |
|---|---|
| `org.axonframework.config.Configuration` | `org.axonframework.common.configuration.Configuration` (read-only) |
| `org.axonframework.queryhandling.QueryBus` | `org.axonframework.messaging.queryhandling.QueryBus` |
| `org.axonframework.queryhandling.QueryUpdateEmitter` | `org.axonframework.messaging.queryhandling.QueryUpdateEmitter` |

## Procedure

### 1. Locate

```bash
grep -RlnE 'org\.axonframework\.config\.Configuration' \
     --include='*.java' --include='*.kt' <target>/src
```

Pick a file that calls `config.queryBus()` / `config.queryUpdateEmitter()` (or `config.findComponent(QueryBus.class)`) on the injected field.

### 2. Switch the injected bean type

- Field type: AF4 `Configuration` → AF5 `Configuration` (`org.axonframework.common.configuration.Configuration`).
- If class also touches root lifecycle → use `AxonConfiguration` (`org.axonframework.common.configuration.AxonConfiguration`).
- Spring constructor injection unchanged on Path A. On Path B, the live `AxonConfiguration` is passed in by the bootstrap that called `configurer.build().start()`.

### 3. Rewrite the AF4 root lookups → AF5

AF4 root lookups returned the bean directly. AF5's `getOptionalComponent(...)` returns `Optional<T>`.

| AF4 call | AF5 replacement |
|---|---|
| `config.queryBus()` | `axonConfig.getOptionalComponent(QueryBus.class).orElseThrow()` |
| `config.queryUpdateEmitter()` | `axonConfig.getOptionalComponent(QueryUpdateEmitter.class).orElseThrow()` |
| `config.findComponent(QueryBus.class)` | `axonConfig.getOptionalComponent(QueryBus.class)` |

Use `.orElseThrow(...)` when AF4 code assumed presence; otherwise propagate the `Optional`.

> **`QueryUpdateEmitter` parameter-injection.** AF5 also exposes `QueryUpdateEmitter` as a `@QueryHandler` method parameter (see the projectors / event-processors doc). If the lookup-via-`Configuration` pattern is used *inside* a handler, prefer the method-parameter form — covered by the main `query-handler` recipe.

### 4. Sweep imports

- Remove stale AF4 imports: `org.axonframework.config.Configuration`, `org.axonframework.queryhandling.QueryBus` / `QueryUpdateEmitter` (package moved).
- Add: `org.axonframework.common.configuration.Configuration` (or `AxonConfiguration`), `org.axonframework.messaging.queryhandling.QueryBus` / `QueryUpdateEmitter`.

## Verify

Invoke the external `axon4to5-isolatedtest` skill compile-only (see [../verification.md](../verification.md)):

```
Skill: axon4to5-isolatedtest
Inputs:
  target-name: <ClassSimpleName>
  build-file: <target>/pom.xml | <target>/build.gradle(.kts)
  main-sources:
    - src/main/java/<…>/<Class>.java
  test-sources: []
  extra-deps:
    - org.axonframework:axon-messaging:${axon5.version}
    - org.axonframework:axon-configuration:${axon5.version}
  cleanup: false
```
