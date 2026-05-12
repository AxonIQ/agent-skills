# `.send(cmd)` returning `CompletableFuture<Void>` / `CompletableFuture<R>`

The most common AF4 shape: `commandGateway.send(cmd)` is assigned to or
returned as a `CompletableFuture<Void>` or `CompletableFuture<R>`. AF4
inferred `<R>` from the assignment context. AF5's `.send(cmd)` returns
`CommandResult` — not a `CompletableFuture` — so the AF4 line will not
compile until rewritten.

The fix is the same in both cases: **add the `R.class` second argument**
to switch to AF5's typed convenience overload `send(Object, Class<R>)`,
which returns `CompletableFuture<R>` directly. Use `Void.class` when
the original was `CompletableFuture<Void>`.

## Variant A — `CompletableFuture<Void>` (no result payload)

Source: `bikerental-extended/payment/.../PaymentController.java`.

### Before (AF4)

```java
import org.axonframework.commandhandling.gateway.CommandGateway;

public class PaymentController {

    private final CommandGateway commandGateway;

    public PaymentController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PostMapping("/acceptPayment")
    public CompletableFuture<Void> confirmPayment(@RequestParam("id") String paymentId) {
        return commandGateway.send(new ConfirmPaymentCommand(paymentId));
    }

    @PostMapping("/rejectPayment")
    public CompletableFuture<Void> rejectPayment(@RequestParam("id") String paymentId) {
        return commandGateway.send(new RejectPaymentCommand(paymentId));
    }
}
```

### After (AF5)

```java
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;

public class PaymentController {

    private final CommandGateway commandGateway;

    public PaymentController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PostMapping("/acceptPayment")
    public CompletableFuture<Void> confirmPayment(@RequestParam("id") String paymentId) {
        return commandGateway.send(new ConfirmPaymentCommand(paymentId), Void.class);
    }

    @PostMapping("/rejectPayment")
    public CompletableFuture<Void> rejectPayment(@RequestParam("id") String paymentId) {
        return commandGateway.send(new RejectPaymentCommand(paymentId), Void.class);
    }
}
```

## Variant B — typed `CompletableFuture<R>`

Source: `bikerental-extended/rental/.../RentalController.java::requestBike`.

### Before (AF4)

```java
import org.axonframework.commandhandling.gateway.CommandGateway;

@PostMapping("/requestBike")
public CompletableFuture<String> requestBike(@RequestParam("bikeId") String bikeId,
                                             @RequestParam(value = "renter", required = false) String renter) {
    return commandGateway.send(new RequestBikeCommand(bikeId, renter != null ? renter : randomRenter()));
}

// elsewhere:
CompletableFuture<RentalReceipt> receipt =
        commandGateway.send(new ConfirmRentalCommand(rentalId));
```

### After (AF5)

```java
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;

@PostMapping("/requestBike")
public CompletableFuture<String> requestBike(@RequestParam("bikeId") String bikeId,
                                             @RequestParam(value = "renter", required = false) String renter) {
    return commandGateway.send(new RequestBikeCommand(bikeId, renter != null ? renter : randomRenter()),
                               String.class);
}

// elsewhere:
CompletableFuture<RentalReceipt> receipt =
        commandGateway.send(new ConfirmRentalCommand(rentalId), RentalReceipt.class);
```

## What changed

- Import: AF4 → AF5 FQN on `CommandGateway`.
- Every AF4 `.send(cmd)` whose return value flows into a
  `CompletableFuture<R>` (return type, assignment, parameter) gains a
  `R.class` second argument. AF5's `send(Object, Class<R>)` is the
  convenience default-method overload that returns `CompletableFuture<R>`
  directly.
- For the `Void` case: `Void.class`.
- Field, constructor, surrounding method signatures — all unchanged.

## Equivalent (longer) form

`commandGateway.send(cmd, R.class)` is shorthand for
`commandGateway.send(cmd).resultAs(R.class)`. Both yield
`CompletableFuture<R>`. Prefer the two-arg overload — fewer characters,
identical semantics.

## Out of scope

Unrelated package moves (e.g., `QueryGateway`'s
`queryhandling.QueryGateway` → `messaging.queryhandling.gateway.QueryGateway`)
that may appear in the same import block belong to other migration
recipes — **flag, do not fix**.
