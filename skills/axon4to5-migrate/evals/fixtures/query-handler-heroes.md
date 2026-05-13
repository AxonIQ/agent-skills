# Eval fixture — `query-handler` on `GetDwellingByIdQueryHandler`

**AF4:** `axon4/heroes/.../creaturerecruitment/read/getdwellingbyid/GetDwellingByIdQueryHandler.java`
**AF5:** `axon5/heroes/.../creaturerecruitment/read/getdwellingbyid/GetDwellingByIdQueryHandler.java`

The simplest case — pure **import-only** rewrite. The body, method signature, return type, and Spring stereotypes stay untouched.

## Trigger

```
/axon4to5-migrate src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/read/getdwellingbyid/GetDwellingByIdQueryHandler.java
```

## Must-haves

- ✅ Import `org.axonframework.queryhandling.QueryHandler` (AF4) → `org.axonframework.messaging.queryhandling.annotation.QueryHandler` (AF5).
- ✅ `@QueryHandler` annotation itself unchanged.
- ✅ Method body, parameter list, return type, visibility — all unchanged.
- ✅ `@Component` annotation untouched (Path A — Spring auto-discovers via `MessageHandlerLookup`).
- ✅ No registration code added (Path A — handled by Spring auto-config).
- ✅ Unused `import java.util.Optional;` may be dropped (was unused in AF4 too); not required, but acceptable.

## Anti-patterns

- ❌ `queryName` attribute changed or dropped.
- ❌ Return type modified.
- ❌ `Configuration` lookup added (this is the handler recipe, not configuration-reads).
- ❌ `QueryHandlingModule` registration code added on Path A (only Path B needs that).

## Output contract

```yaml
result: success
target: com.dddheroes.heroesofddd.creaturerecruitment.read.getdwellingbyid.GetDwellingByIdQueryHandler
decisions:
  path: A (Spring Boot)
  configurer-registration: auto-spring
caller-expects: { commit: true, next: proceed }
```
