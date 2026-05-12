# Controller orchestrating multiple sends (`.allOf`, chains)

A controller that chains sends, aggregates futures via
`CompletableFuture.allOf`, or pipes results through
`.thenCompose(...)`. Each send needs its own rewrite to recover a
`CompletableFuture` from `CommandResult`.

Source: bikerental-extended `RentalController.java`.

## Before (AF4) — fragments

```java
import org.axonframework.commandhandling.gateway.CommandGateway;
// ...

// 1) aggregating multiple fire-and-forget sends with .allOf
@PostMapping("/bikes")
public CompletableFuture<Void> generateBikes(@RequestParam("count") int bikeCount,
                                             @RequestParam("type") String bikeType) {
    CompletableFuture<Void> all = CompletableFuture.completedFuture(null);
    for (int i = 0; i < bikeCount; i++) {
        all = CompletableFuture.allOf(all,
                commandGateway.send(new RegisterBikeCommand(UUID.randomUUID().toString(),
                                                            bikeType,
                                                            randomLocation())));
    }
    return all;
}

// 2) typed CompletableFuture<String> result
@PostMapping("/requestBike")
public CompletableFuture<String> requestBike(@RequestParam("bikeId") String bikeId,
                                             @RequestParam(value = "renter", required = false) String renter) {
    return commandGateway.send(new RequestBikeCommand(bikeId, renter != null ? renter : randomRenter()));
}

// 3) inside a reactive chain
private Mono<String> executeRentalCycle(String bikeType, String renter, int abandonPaymentFactor, int delay) {
    CompletableFuture<String> result = selectRandomAvailableBike(bikeType)
            .thenCompose(bikeId -> commandGateway.send(new RequestBikeCommand(bikeId, renter))
                                                 .thenComposeAsync(paymentRef -> /* ... */)
                                                 .thenCompose(r -> whenBikeUnlocked(bikeId))
                                                 .thenComposeAsync(r -> commandGateway.send(new ReturnBikeCommand(
                                                                          bikeId, randomLocation())),
                                                                   /* ... */)
                                                 .thenApply(r -> bikeId));
    return Mono.fromFuture(result);
}
```

## After (AF5) — fragments

```java
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
// ...

// 1) aggregating multiple fire-and-forget sends with .allOf
@PostMapping("/bikes")
public CompletableFuture<Void> generateBikes(@RequestParam("count") int bikeCount,
                                             @RequestParam("type") String bikeType) {
    CompletableFuture<Void> all = CompletableFuture.completedFuture(null);
    for (int i = 0; i < bikeCount; i++) {
        all = CompletableFuture.allOf(all,
                commandGateway.send(new RegisterBikeCommand(UUID.randomUUID().toString(),
                                                            bikeType,
                                                            randomLocation()))
                              .getResultMessage());
    }
    return all;
}

// 2) typed CompletableFuture<String> result
@PostMapping("/requestBike")
public CompletableFuture<String> requestBike(@RequestParam("bikeId") String bikeId,
                                             @RequestParam(value = "renter", required = false) String renter) {
    return commandGateway.send(new RequestBikeCommand(bikeId, renter != null ? renter : randomRenter()))
                         .resultAs(String.class);
}

// 3) inside a reactive chain
private Mono<String> executeRentalCycle(String bikeType, String renter, int abandonPaymentFactor, int delay) {
    CompletableFuture<String> result = selectRandomAvailableBike(bikeType)
            .thenCompose(bikeId -> commandGateway.send(new RequestBikeCommand(bikeId, renter))
                                                 .resultAs(String.class)
                                                 .thenComposeAsync(rentalRef -> /* ... */
                                                                    .thenComposeAsync(r -> commandGateway.send(new ReturnBikeCommand(
                                                                                                  bikeId, randomLocation()))
                                                                                              .getResultMessage(),
                                                                                      /* ... */)
                                                                    .thenApply(r -> bikeId),
                                                                   /* ... */));
    return Mono.fromFuture(result);
}
```

## What changed

- `.allOf(... commandGateway.send(cmd))` (fragment 1) — `.allOf`
  expects `CompletableFuture<?>`, but AF5's `.send(cmd)` is now
  `CommandResult`. Append `.getResultMessage()` to get the
  `CompletableFuture<? extends Message>` `.allOf` accepts.
  Alternative: `.send(cmd, Void.class)` if you don't care about the
  result message.
- `.send(cmd)` returning typed `CompletableFuture<R>` (fragment 2) —
  add the result-class arg: `.send(cmd, String.class)` (preferred
  shorthand), or `.send(cmd).resultAs(String.class)`.
- `.send(cmd).thenCompose(...)` style chains (fragment 3) — insert
  `.resultAs(R.class)` (or `.getResultMessage()`) between `.send(...)`
  and the `.thenCompose...` to get back a real `CompletableFuture`.
- Field, constructor, and the surrounding method signatures are
  preserved. Only the dispatch lines change.

## Choosing between `.resultAs(R.class)`, `.send(cmd, R.class)`, and `.getResultMessage()`

| Want | Use |
|---|---|
| `CompletableFuture<R>` for typed payload, no metadata | `.send(cmd, R.class)` (default-method shorthand — cleanest) |
| `CompletableFuture<R>` for typed payload, with metadata | `.send(cmd, metadata).resultAs(R.class)` |
| Fire-and-forget composition (`.allOf`, `.thenRun`, etc.) | `.send(cmd).getResultMessage()` |
| Need the result `Message` itself (metadata, identifier) | `.getResultMessage().thenApply(m -> ...)` |
| Chain with `.onSuccess(...)` / `.onError(...)` callbacks | leave as `CommandResult` (don't unwrap) |
