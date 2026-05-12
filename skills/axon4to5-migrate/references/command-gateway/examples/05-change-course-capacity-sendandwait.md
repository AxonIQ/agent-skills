# `sendAndWait(...)` and the timeout-overload rewrite

AF5 keeps `sendAndWait(...)` in two arities (`cmd` and `cmd, R.class`).
The 3-arity timeout overload is gone.

**Default rule: prefer non-blocking.** If the surrounding caller can
accept a `CompletableFuture<R>` (Spring controller, reactive method,
or any caller that already composes futures), rewrite to
`commandGateway.send(cmd, R.class)` and change the method's return
type. Spring serves `CompletableFuture<R>` async out of the box —
identical HTTP behavior, no request-thread blocking. Keep `sendAndWait`
only when the caller genuinely cannot accept a future
(`CommandLineRunner`, `ApplicationRunner`, `@Scheduled void`, `main`,
or tests asserting on the return).

## Variant A — Spring controller: PREFER converting to async

This is the dominant case in real codebases.

### Before (AF4)

```java
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
// ...

@RestController
@RequestMapping("/api/courses")
public class ChangeCourseCapacityController {

    private final CommandGateway commandGateway;

    public ChangeCourseCapacityController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PutMapping("/{courseId}/capacity")
    public ResponseEntity<Void> changeCapacity(@PathVariable String courseId,
                                               @RequestBody ChangeCourseCapacityRequest request) {
        commandGateway.sendAndWait(new ChangeCourseCapacity(courseId, request.capacity()));
        return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
    }
}
```

### After (AF5) — preferred non-blocking rewrite

```java
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.concurrent.CompletableFuture;
// ...

@RestController
@RequestMapping("/api/courses")
public class ChangeCourseCapacityController {

    private final CommandGateway commandGateway;

    public ChangeCourseCapacityController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PutMapping("/{courseId}/capacity")
    public CompletableFuture<ResponseEntity<Void>> changeCapacity(@PathVariable String courseId,
                                                                  @RequestBody ChangeCourseCapacityRequest request) {
        return commandGateway.send(new ChangeCourseCapacity(courseId, request.capacity()), Void.class)
                             .thenApply(v -> ResponseEntity.status(HttpStatus.NO_CONTENT).build());
    }
}
```

What changed:
- Import: AF4 → AF5 FQN.
- Return type: `ResponseEntity<Void>` → `CompletableFuture<ResponseEntity<Void>>`.
- Call: `sendAndWait(cmd)` → `send(cmd, Void.class)`.
- Result composed via `.thenApply(...)`. Caller-visible HTTP behavior
  is unchanged.
- Spring MVC and WebFlux both handle `CompletableFuture<R>` natively
  (Servlet 3 async dispatch / reactive bridge respectively). No extra
  configuration needed.

### Variants for typed responses

```java
// Returning a typed body
public CompletableFuture<MyResponse> handle(...) {
    return commandGateway.send(new MyCommand(...), MyResponse.class);
}

// Body returned directly (Spring wraps with 200 OK)
public CompletableFuture<RentalReceipt> rent(...) {
    return commandGateway.send(new RentCommand(...), RentalReceipt.class);
}
```

## Variant B — `CommandLineRunner` / `@Scheduled` / `main` / test: keep blocking

These callers cannot accept a future. Only the import changes.

### Before (AF4) → After (AF5)

```java
// AF4
import org.axonframework.commandhandling.gateway.CommandGateway;

@Bean
ApplicationRunner runner(CommandGateway commandGateway) {
    return args -> {
        String id = UUID.randomUUID().toString();
        commandGateway.sendAndWait(new CreateCourse(id, "Foo" + System.currentTimeMillis()));
    };
}

String result = commandGateway.sendAndWait(new CreatePayment(ref), String.class);
```

```java
// AF5 — only the import differs
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;

@Bean
ApplicationRunner runner(CommandGateway commandGateway) {
    return args -> {
        String id = UUID.randomUUID().toString();
        commandGateway.sendAndWait(new CreateCourse(id, "Foo" + System.currentTimeMillis()));
    };
}

String result = commandGateway.sendAndWait(new CreatePayment(ref), String.class);
```

## Variant C — `sendAndWait(cmd, timeout, unit)` (AF4 only)

AF4's 3-arity timeout overload is gone in AF5. Two replacement shapes.

### Preferred (caller accepts a future)

```java
// AF4
String result = commandGateway.sendAndWait(new CreatePayment(ref), 5, TimeUnit.SECONDS);

// AF5 — non-blocking, with timeout
CompletableFuture<String> result = commandGateway.send(new CreatePayment(ref), String.class)
                                                 .orTimeout(5, TimeUnit.SECONDS);
```

Adapt the surrounding method's return type to `CompletableFuture<R>`
the same way as Variant A.

### Fallback (caller really must block)

```java
// AF4
String result = commandGateway.sendAndWait(new CreatePayment(ref), 5, TimeUnit.SECONDS);

// AF5 — blocking, with timeout (still better than .join() with no timeout)
String result = commandGateway.send(new CreatePayment(ref), String.class)
                              .orTimeout(5, TimeUnit.SECONDS)
                              .join();
```

This matches AF5's own framework rule: never `.join()` / `.get()`
without a timeout — silently turns transient issues (pool exhaustion,
deadlock, partition) into permanent thread leaks.

## Decision: which variant to use

```
Is the caller of the migrated method one of:
  - Spring @RestController / @Controller method?       → Variant A (async)
  - reactive method (Mono / Flux / Publisher)?         → Variant A (async, with bridge)
  - any method already returning CompletableFuture<R>? → Variant A (async)
  - CommandLineRunner / ApplicationRunner?             → Variant B (keep blocking)
  - @Scheduled void / void main?                       → Variant B (keep blocking)
  - integration test asserting on the return?          → Variant B (keep blocking)
  - had AF4 sendAndWait(cmd, timeout, unit)?           → Variant C (preferred or fallback)
```

If unsure, default to Variant A and let the surrounding compile error
tell you whether the caller accepts a future. Reverting to Variant B
is mechanical (drop the `CompletableFuture<...>` wrapper, replace
`.send(cmd, R.class)` with `.sendAndWait(cmd, R.class)`).
