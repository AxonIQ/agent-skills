# CommandGateway — Top-Level Dispatchers (REST/MCP/CLI)

Top-level entry points (REST controllers, MCP tools, CLI runners, scheduled jobs) keep using `CommandGateway` in
AF5 — they have no `ProcessingContext`, so they cannot switch to `CommandDispatcher` (which is the in-handler
pattern, see [command-dispatcher.md](command-dispatcher.md)). What changes is the **API shape**:
`.send(cmd)` now returns `CommandResult` (not `CompletableFuture` directly), so callers must chain
`.resultAs(<Type>.class)` to get a `CompletableFuture<Type>`. `.sendAndWait(cmd)` is removed — block by
chaining `.resultAs(...).orTimeout(...).join()` (or whatever the caller's blocking contract demands).

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.commandhandling.gateway.CommandGateway` | `org.axonframework.messaging.commandhandling.gateway.CommandGateway` |
| `org.axonframework.commandhandling.GenericCommandMessage` | *(usually removed — send plain payloads)* |

## Detection

**Pre-migration (AF4 original):**

```bash
# Top-level classes that inject CommandGateway but are NOT event handlers
grep -rln '\bCommandGateway\b\|import.*commandhandling\.gateway\.CommandGateway' \
  --include='*.java' --include='*.kt' --include='*.scala' . \
  | xargs grep -L '@EventHandler'

# sendAndWait callers (must be rewritten — no AF5 equivalent)
grep -rn '\.sendAndWait\s*(' --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
# AF5 import landed, but chain still calls .thenApply / .get on .send() —
# won't compile because .send() now returns CommandResult, not CompletableFuture.
grep -rln 'org\.axonframework\.messaging\.commandhandling\.gateway\.CommandGateway' \
  --include='*.java' --include='*.kt' --include='*.scala' . \
  | xargs grep -nE '\.send\([^)]*\)\s*\.(thenApply|thenCompose|thenAccept|get|join)'
```

## Axon Framework 4 Code

```java
import org.axonframework.commandhandling.gateway.CommandGateway;

@RestController
@RequestMapping("games/{gameId}")
class BuildDwellingRestApi {

    private final CommandGateway commandGateway;

    BuildDwellingRestApi(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    // Async: returns CompletableFuture directly
    @PutMapping("/dwellings/{dwellingId}")
    CompletableFuture<Void> putDwellings(@PathVariable String dwellingId, @RequestBody Body body) {
        var command = BuildDwelling.command(dwellingId, body.creatureId(), body.costPerTroop());
        return commandGateway.send(command);
    }

    // Sync: blocks and returns the result
    @PostMapping("/dwellings")
    String createDwelling(@RequestBody Body body) {
        return commandGateway.sendAndWait(BuildDwelling.command(body.id(), body.creatureId(), body.costPerTroop()));
    }
}
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;

import java.util.concurrent.TimeUnit;

@RestController
@RequestMapping("games/{gameId}")
class BuildDwellingRestApi {

    private final CommandGateway commandGateway;

    BuildDwellingRestApi(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    // Async: .send() returns CommandResult — call .resultAs(Type.class) to get CompletableFuture<Type>
    @PutMapping("/dwellings/{dwellingId}")
    CompletableFuture<Void> putDwellings(@PathVariable String dwellingId, @RequestBody Body body) {
        var command = BuildDwelling.command(dwellingId, body.creatureId(), body.costPerTroop());
        return commandGateway.send(command).resultAs(Void.class);
    }

    // Sync: chain .resultAs + .orTimeout(...).join() — sendAndWait is gone
    @PostMapping("/dwellings")
    String createDwelling(@RequestBody Body body) {
        return commandGateway
                .send(BuildDwelling.command(body.id(), body.creatureId(), body.costPerTroop()))
                .resultAs(String.class)
                .orTimeout(30, TimeUnit.SECONDS)
                .join();
    }
}
```

## Rules

- **Top-level dispatchers (REST/MCP/CLI/scheduled) KEEP `CommandGateway`.** Do NOT switch to `CommandDispatcher` —
  that only works inside a `ProcessingContext`.
- **`.send(cmd)` returns `CommandResult`** — chain `.resultAs(<Type>.class)` to get a `CompletableFuture<Type>`.
  Use `Void.class` when the command has no return payload.
- **`.sendAndWait(cmd)` is gone** — replace with `.send(cmd).resultAs(<Type>.class).orTimeout(<n>, SECONDS).join()`.
  The timeout choice is **caller-specific**: REST controllers typically use a small per-request budget; CLI runners
  may use a longer or unbounded wait. Pick what matches the original `sendAndWait` semantics in your code.
- **Update the import** to `org.axonframework.messaging.commandhandling.gateway.CommandGateway` (the `.messaging.`
  infix). The OpenRewrite `ChangePackage` rule does this automatically — see the partial state below.
- **`GenericCommandMessage` wrapping is usually unnecessary** — send plain command payloads. Keep
  `GenericCommandMessage` only if you need to attach metadata via the message constructor; otherwise pass the
  payload directly.

## Partial migration state (post-OpenRewrite)

OpenRewrite's `axon4-to-axon5-messaging.yml` runs a top-level `ChangePackage` from
`org.axonframework.commandhandling` → `org.axonframework.messaging.commandhandling`, so the **import** is
rewritten automatically. There is **no** OpenRewrite rule that rewrites the `.send(...)` / `.sendAndWait(...)`
chain — `MigrateCommandGatewayInEventHandler` only targets `@EventHandler` classes, not top-level dispatchers.

After OR runs, expect this half-state in REST/MCP/CLI classes:

- ✅ Import on the AF5 `…messaging.commandhandling.gateway.CommandGateway` path.
- ❌ Body still calls `.sendAndWait(cmd)` (does not compile — method removed).
- ❌ Body still chains `.send(cmd).thenApply(...)` / `.thenCompose(...)` / `.get()` (does not compile —
  `.send()` now returns `CommandResult`, not `CompletableFuture`).

AI completes the gap by inserting `.resultAs(<Type>.class)` between `.send(cmd)` and the downstream chain, and by
rewriting `.sendAndWait(cmd)` to `.send(cmd).resultAs(<Type>.class).orTimeout(...).join()`.

## Notes

- **OpenRewrite status:** Partial — `ChangePackage` in `axon4-to-axon5-messaging.yml` moves the `CommandGateway`
  import to the `.messaging.` path; AI rewrites the `.send()`/`.sendAndWait()` call chains (insert `.resultAs(...)`,
  replace `.sendAndWait` with `.send().resultAs().orTimeout().join()`).
- For in-handler dispatch (a class with `@EventHandler` that dispatches commands), see
  [command-dispatcher.md](command-dispatcher.md) — that pattern switches to `CommandDispatcher`; this one keeps
  `CommandGateway`.
