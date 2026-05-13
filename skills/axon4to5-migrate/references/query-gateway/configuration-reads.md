# Query-bus configuration reads

Rare — most projects inject `QueryGateway` / `QueryUpdateEmitter` directly. Use this when a class reaches through AF4 `Configuration#queryBus()` / `queryUpdateEmitter()`.

## FQN cheat sheet

| AF4 | AF5 |
|---|---|
| `org.axonframework.config.Configuration` | `org.axonframework.common.configuration.Configuration` (read-only) |
| `org.axonframework.queryhandling.QueryBus` | `org.axonframework.messaging.queryhandling.QueryBus` |
| `org.axonframework.queryhandling.QueryUpdateEmitter` | `org.axonframework.messaging.queryhandling.QueryUpdateEmitter` |

## Procedure

### Step 1 — Locate

```bash
grep -RlnE 'org\.axonframework\.config\.Configuration' --include='*.java' --include='*.kt' <target>/src
```

Pick a file calling `config.queryBus()` / `config.queryUpdateEmitter()` / `config.findComponent(QueryBus.class)`.

### Step 2 — Switch injected type

AF4 `Configuration` → AF5 `Configuration`. If class touches root lifecycle → use `AxonConfiguration`. Path A: Spring injection unchanged. Path B: pass `AxonConfiguration` from `configurer.build().start()`.

### Step 3 — Rewrite root lookups

| AF4 | AF5 |
|---|---|
| `config.queryBus()` | `axonConfig.getOptionalComponent(QueryBus.class).orElseThrow()` |
| `config.queryUpdateEmitter()` | `axonConfig.getOptionalComponent(QueryUpdateEmitter.class).orElseThrow()` |
| `config.findComponent(QueryBus.class)` | `axonConfig.getOptionalComponent(QueryBus.class)` |

> If lookup-via-`Configuration` is used **inside a `@QueryHandler` method**, prefer the AF5 method-parameter form — covered by the `query-handler` recipe.

### Step 4 — Sweep imports

Remove AF4 `org.axonframework.config.Configuration` and `org.axonframework.queryhandling.QueryBus` / `QueryUpdateEmitter`. Add AF5 equivalents.

## Verify

```
target-name: <ClassSimpleName>
main-sources: [<Class>.java]
test-sources: []
extra-deps: [axon-messaging, axon-configuration]
```
