# Kotlin REST controller variant

The rewrite shapes for Kotlin are identical to Java — same imports,
same `CommandResult` → `CompletableFuture` recovery options. Kotlin
syntax differences (`val`, primary constructors, expression bodies,
trailing-lambda style for `.onSuccess`/`.onError`) only.

## Before (AF4)

```kotlin
package io.example.rental.ui

import io.example.rental.coreapi.ConfirmPaymentCommand
import io.example.rental.coreapi.RejectPaymentCommand
import io.example.rental.coreapi.RequestBikeCommand
import org.axonframework.commandhandling.gateway.CommandGateway
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RestController
import java.util.concurrent.CompletableFuture

@RestController
class PaymentController(private val commandGateway: CommandGateway) {

    @PostMapping("/acceptPayment")
    fun confirmPayment(@RequestParam("id") paymentId: String): CompletableFuture<Void> =
        commandGateway.send(ConfirmPaymentCommand(paymentId))

    @PostMapping("/rejectPayment")
    fun rejectPayment(@RequestParam("id") paymentId: String): CompletableFuture<Void> =
        commandGateway.send(RejectPaymentCommand(paymentId))

    @PostMapping("/requestBike")
    fun requestBike(@RequestParam("bikeId") bikeId: String,
                    @RequestParam("renter") renter: String): CompletableFuture<String> =
        commandGateway.send(RequestBikeCommand(bikeId, renter))
}
```

## After (AF5)

```kotlin
package io.example.rental.ui

import io.example.rental.coreapi.ConfirmPaymentCommand
import io.example.rental.coreapi.RejectPaymentCommand
import io.example.rental.coreapi.RequestBikeCommand
import org.axonframework.messaging.commandhandling.gateway.CommandGateway
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RestController
import java.util.concurrent.CompletableFuture

@RestController
class PaymentController(private val commandGateway: CommandGateway) {

    @PostMapping("/acceptPayment")
    fun confirmPayment(@RequestParam("id") paymentId: String): CompletableFuture<Void> =
        commandGateway.send(ConfirmPaymentCommand(paymentId), Void::class.java)

    @PostMapping("/rejectPayment")
    fun rejectPayment(@RequestParam("id") paymentId: String): CompletableFuture<Void> =
        commandGateway.send(RejectPaymentCommand(paymentId), Void::class.java)

    @PostMapping("/requestBike")
    fun requestBike(@RequestParam("bikeId") bikeId: String,
                    @RequestParam("renter") renter: String): CompletableFuture<String> =
        commandGateway.send(RequestBikeCommand(bikeId, renter), String::class.java)
}
```

## What changed

- Import: AF4 → AF5 FQN.
- Kotlin uses `T::class.java` where Java uses `T.class`:
  - Java `commandGateway.send(cmd, String.class)`
  - Kotlin `commandGateway.send(cmd, String::class.java)`
- Same option matrix as Java for choosing among `.send(cmd, R::class.java)`,
  `.send(cmd, metadata).resultAs(R::class.java)`, and
  `.send(cmd).getResultMessage()`.
- Kotlin trailing-lambda `.onSuccess { ... }` / `.onError { ... }`
  works for the callback shape (example 04).
- For `Void`, prefer `Void::class.java` (or the lower-cased
  `Unit::class.java` is **not** equivalent — keep `Void::class.java`
  to match the AF4 typing, otherwise the result-type contract changes).

## Note for the LLM running this recipe

If the candidate file is Kotlin, translate the Java rewrite shapes
mechanically: replace `R.class` with `R::class.java`, keep the rest as
in the Java examples. Do not introduce Kotlin idioms beyond what the
syntax requires (no `coroutines`, no `await()` — that's a refactor,
not a migration).
