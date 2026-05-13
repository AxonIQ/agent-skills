# Scenario 02 — SINGLE: exclude-when keeps a handler out of `command-gateway`

## Starting state

- Project: AF4 Spring Boot. Pinned decisions in place.
- File `RentalSaga.java` injects `CommandGateway` AND declares `@EventHandler` methods.

## User input

```
/axon4to5-migrate src/main/java/com/example/rental/RentalSaga.java
```

## Expected behavior

1. Mode: SINGLE.
2. Routing walks rows in phase order:
   - `aggregate` — no `@Aggregate` annotation, no match.
   - `event-processor` — `@EventHandler` matches, no exclude-when defined for this row → row wins at phase 3.
3. Even though `command-gateway`'s discovery grep `CommandGateway` matches the import, its `exclude-when` (`@EventHandler\|@CommandHandler\|@QueryHandler\|@MessageHandlerInterceptor`) fires → `command-gateway` is NOT chosen.
4. `event-processor` recipe runs; commit follows.

## Pass / fail signals

- ✅ Pass: the file is migrated through `event-processor`, not `command-gateway`.
- ❌ Fail: orchestrator routes to `command-gateway` because `CommandGateway` import was matched without honoring `exclude-when`.

## Why this matters

Classes that inject a gateway AND handle messages belong to the handler recipe (the gateway use is incidental). Without `exclude-when` semantics, a saga or handler would be rewritten with the wrong recipe and lose its handler-side migration.
