**Result:** ✅ Success
**Source:** `io.axoniq.demo.gamerental.command.Game`
**Recipe:** axon4to5-aggregate

**Notes:** Migrated AF4 aggregate `Game` to AF5 Path A (Spring) shape. Constructor-style `@CommandHandler public Game(RegisterGameCommand)` rewritten per use-case 03 Pattern 3: split into `@EntityCreator public Game(GameRegisteredEvent)` (absorbs the matching `@EventSourcingHandler(GameRegisteredEvent)` body, which is removed) and a static `@CommandHandler` factory `handle(RegisterGameCommand, EventAppender)`. Instance command handlers receive `EventAppender appender`; `apply(...)` calls replaced with `appender.append(...)`. `@AggregateIdentifier`, AF4 `@Aggregate`, AF4 `@CommandHandler`/`@EventSourcingHandler` imports, and the `AggregateLifecycle` static import removed. `@Profile("command")` (Spring) and `@ExceptionHandler` (Axon interceptor) preserved verbatim. Class-level `@EventSourced(tagKey = "Game", idType = String.class)` emitted explicitly.

**Learnings:**
- Pattern 3 collapses the AF4 framework-only no-arg constructor + `@EventSourcingHandler(GameRegisteredEvent)` body into a single `@EntityCreator(GameRegisteredEvent)` constructor — leaving the original ESH in place would double-seed state on replay.
- `@ExceptionHandler` (`org.axonframework.messaging.interceptors.ExceptionHandler`) is an Axon interceptor whose package survives unchanged into AF5 — preserved as-is; no rewrite needed.
