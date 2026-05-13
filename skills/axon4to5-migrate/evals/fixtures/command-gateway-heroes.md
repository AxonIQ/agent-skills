# Eval fixture — `command-gateway` on `RecruitCreatureRestApi`

**AF4:** `axon4/heroes/.../creaturerecruitment/write/recruitcreature/RecruitCreatureRestApi.java`
**AF5:** `axon5/heroes/.../creaturerecruitment/write/recruitcreature/RecruitCreatureRestApi.java`

Spring `@RestController` that takes a PUT, builds a command, and returns `CompletableFuture<Void>`.

## Trigger

```
/axon4to5-migrate src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/write/recruitcreature/RecruitCreatureRestApi.java
```

## Must-haves

- ✅ Import: `org.axonframework.commandhandling.gateway.CommandGateway` (AF4) → `org.axonframework.messaging.commandhandling.gateway.CommandGateway` (AF5). Single-line import change.
- ✅ Field type, constructor, variable name unchanged (still `CommandGateway commandGateway`).
- ✅ Controller method return type stays `CompletableFuture<Void>` (was already future-shaped in AF4; AF5 preserves that).
- ✅ Inside the method body: `commandGateway.send(command, GameMetaData.with(...))` rewritten so the result is a `CompletableFuture<Void>` — either via `.resultAs(Void.class)` OR via the `.send(cmd, Void.class)` shorthand. The AF5 reference for this controller uses the same shape; what matters is **no leftover assignment of `CommandResult` to a `CompletableFuture` variable**.
- ✅ NO `CommandDispatcher` introduced (top-of-chain caller — gateway stays).
- ✅ Spring stereotypes (`@RestController`, `@RequestMapping`, `@PutMapping`, etc.) untouched.

## Anti-patterns

- ❌ `CommandGateway` replaced with `CommandDispatcher` (wrong for top-of-chain).
- ❌ `CompletableFuture<X> = commandGateway.send(cmd[, metadata])` left as-is — `CommandResult` is NOT a `CompletableFuture` in AF5 and this compiles in AF4 but FAILS in AF5.
- ❌ `sendAndWait(...)` introduced in a future-friendly controller (regression to blocking).
- ❌ `Mono.fromFuture(commandGateway.send(cmd))` direct — needs `.resultAs(R.class)` first.

## Output contract

```yaml
result: success
target: com.dddheroes.heroesofddd.creaturerecruitment.write.recruitcreature.RecruitCreatureRestApi
decisions:
  path: A (Spring Boot)
  return-shape: mvc
caller-expects: { commit: true, next: proceed }
```
