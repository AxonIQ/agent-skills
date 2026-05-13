# Command-bus configuration reads

Rare — most projects inject `CommandGateway` directly. Use this when a class reaches through AF4 `Configuration#commandBus()` to dispatch low-level command messages or wire interceptors at runtime.

## FQN cheat sheet

| AF4 | AF5 |
|---|---|
| `org.axonframework.config.Configuration` | `org.axonframework.common.configuration.Configuration` (read-only) |
| `org.axonframework.commandhandling.CommandBus` | `org.axonframework.messaging.commandhandling.CommandBus` |

## Procedure

### Step 1 — Locate

```bash
grep -RlnE 'org\.axonframework\.config\.Configuration' --include='*.java' --include='*.kt' <target>/src
```

Pick a file calling `config.commandBus()` or `config.findComponent(CommandBus.class)`.

### Step 2 — Switch injected type

- AF4 `Configuration` → AF5 `Configuration`.
- If class also touches root lifecycle → use `AxonConfiguration` instead.
- Path A: Spring injection unchanged. Path B: pass `AxonConfiguration` from `configurer.build().start()`.

### Step 3 — Rewrite root lookup

AF4 root lookups returned the bean directly. AF5 `getOptionalComponent(...)` returns `Optional<T>`.

| AF4 | AF5 |
|---|---|
| `config.commandBus()` | `axonConfig.getOptionalComponent(CommandBus.class).orElseThrow()` |
| `config.findComponent(CommandBus.class)` | `axonConfig.getOptionalComponent(CommandBus.class)` |

Use `.orElseThrow(...)` when AF4 assumed presence; otherwise propagate the `Optional`.

### Step 4 — Sweep imports

Remove AF4 `org.axonframework.config.Configuration` and `org.axonframework.commandhandling.CommandBus`. Add AF5 equivalents.

## Verify

```
target-name: <ClassSimpleName>
main-sources: [<Class>.java]
test-sources: []
extra-deps: [axon-messaging, axon-configuration]
```
