# Command-bus configuration reads

Read-side migration for a class that **injects AF4 `Configuration` to look up `CommandBus`**. Rare — most projects inject `CommandGateway` directly. Use this when a Spring `@Component` / service reaches through `Configuration#commandBus()` to dispatch low-level command messages or wire interceptors at runtime.

Used by the main `command-gateway` recipe as a sub-reference when the candidate is a configuration **reader**, not a top-of-chain `CommandGateway` caller.

## Canonical reference

- [../../docs/paths/configuration.adoc](../../docs/paths/configuration.adoc) — `Configurer` split, `AxonConfiguration` / `Configuration`, component lookup model.
- [../../docs/paths/index.adoc](../../docs/paths/index.adoc) §"Import and package changes" — `org.axonframework.config` → `org.axonframework.common.configuration`.

## Goal

- Injected bean changed from AF4 `Configuration` (`org.axonframework.config.Configuration`) to AF5 `Configuration` (`org.axonframework.common.configuration.Configuration`) — or `AxonConfiguration` when the class also touches root lifecycle.
- AF4 `config.commandBus()` rewritten to AF5 root-scoped lookup.

## FQN cheat sheet

| AF4 | AF5 |
|---|---|
| `org.axonframework.config.Configuration` | `org.axonframework.common.configuration.Configuration` (read-only) |
| `org.axonframework.commandhandling.CommandBus` | `org.axonframework.messaging.commandhandling.CommandBus` |

## Procedure

### 1. Locate

```bash
grep -RlnE 'org\.axonframework\.config\.Configuration' \
     --include='*.java' --include='*.kt' <target>/src
```

Pick a file that calls `config.commandBus()` (or `config.findComponent(CommandBus.class)`) on the injected field.

### 2. Switch the injected bean type

- Field type: AF4 `Configuration` → AF5 `Configuration` (`org.axonframework.common.configuration.Configuration`).
- If class also touches root lifecycle → use `AxonConfiguration` (`org.axonframework.common.configuration.AxonConfiguration`) instead.
- Spring constructor injection unchanged on Path A. On Path B, the live `AxonConfiguration` is passed in by the bootstrap that called `configurer.build().start()`.

### 3. Rewrite the AF4 root lookup → AF5

AF4 root lookups (`commandBus()`) returned the bean directly. AF5's `getOptionalComponent(...)` returns `Optional<T>`.

| AF4 call | AF5 replacement |
|---|---|
| `config.commandBus()` | `axonConfig.getOptionalComponent(CommandBus.class).orElseThrow()` |
| `config.findComponent(CommandBus.class)` | `axonConfig.getOptionalComponent(CommandBus.class)` |

Use `.orElseThrow(...)` when AF4 code assumed presence; otherwise propagate the `Optional`.

### 4. Sweep imports

- Remove stale AF4 imports: `org.axonframework.config.Configuration`, `org.axonframework.commandhandling.CommandBus` (package moved).
- Add: `org.axonframework.common.configuration.Configuration` (or `AxonConfiguration`), `org.axonframework.messaging.commandhandling.CommandBus`.

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
