# Eval fixture — `query-gateway` on `GetAllDwellingsMcp`

**AF4:** `axon4/heroes/.../creaturerecruitment/read/getalldwellings/GetAllDwellingsMcp.java`
**AF5:** `axon5/heroes/.../creaturerecruitment/read/getalldwellings/GetAllDwellingsMcp.java`

MCP resource handler (synchronous framework callback). The query runs inside a lambda that MUST return synchronously, so a `.orTimeout(...).join()` bridge is the correct AF5 shape.

## Trigger

```
/axon4to5-migrate src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/read/getalldwellings/GetAllDwellingsMcp.java
```

## Must-haves

- ✅ Import: `org.axonframework.queryhandling.QueryGateway` (AF4) → `org.axonframework.messaging.queryhandling.gateway.QueryGateway` (AF5).
- ✅ Field type, constructor, variable name unchanged.
- ✅ AF4 `queryGateway.query(query, GetAllDwellings.Result.class).get()` rewritten to **timed blocking**:
  ```java
  queryGateway.query(query, GetAllDwellings.Result.class)
              .orTimeout(30, TimeUnit.SECONDS)
              .join();
  ```
- ✅ Import `java.util.concurrent.TimeUnit` added (needed for the timeout).
- ✅ NO bare `.get()` / `.join()` left in the file.
- ✅ NO `ResponseType` / `ResponseTypes.*` introduced (file didn't have them; recipe must not add them).
- ✅ Spring stereotypes (`@Component`, `@Bean`, etc.) untouched.

## Anti-patterns

- ❌ `.get()` left in place (no timeout = potential indefinite block).
- ❌ Introducing `Mono.fromFuture(...)` in a synchronous MCP callback (wrong shape — callback signature requires sync return).
- ❌ `ResponseTypes.instanceOf(...)` introduced (SPI removed in AF5).
- ❌ `queryGateway` replaced with `queryBus` lookup via `Configuration` (wrong recipe; this is the gateway recipe, not configuration-reads).

## Output contract

```yaml
result: success
target: com.dddheroes.heroesofddd.creaturerecruitment.read.getalldwellings.GetAllDwellingsMcp
decisions:
  path: A (Spring Boot)
  query-shape: single
caller-expects: { commit: true, next: proceed }
```
