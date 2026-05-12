# AF4 `CommandCallback` SPI → AF5 `.onSuccess` / `.onError`

AF4 had a `send(cmd, callback)` overload taking a `CommandCallback`
SPI. AF5 removed the SPI; the idiomatic equivalent is
`.onSuccess(...)` / `.onError(...)` on the `CommandResult`.

## Before (AF4)

```java
import org.axonframework.commandhandling.CommandCallback;
import org.axonframework.commandhandling.CommandMessage;
import org.axonframework.commandhandling.CommandResultMessage;
import org.axonframework.commandhandling.gateway.CommandGateway;
// ...

public class RentalDispatcher {

    private final CommandGateway commandGateway;

    public RentalDispatcher(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    public void requestBike(RequestBikeCommand cmd) {
        commandGateway.send(cmd, new CommandCallback<RequestBikeCommand, String>() {
            @Override
            public void onResult(CommandMessage<? extends RequestBikeCommand> commandMessage,
                                 CommandResultMessage<? extends String> commandResultMessage) {
                if (commandResultMessage.isExceptional()) {
                    log.error("Failed to request bike", commandResultMessage.exceptionResult());
                } else {
                    log.info("Bike requested, rentalRef={}", commandResultMessage.getPayload());
                }
            }
        });
    }
}
```

## After (AF5)

```java
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
// ...

public class RentalDispatcher {

    private final CommandGateway commandGateway;

    public RentalDispatcher(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    public void requestBike(RequestBikeCommand cmd) {
        commandGateway.send(cmd)
                      .onSuccess(String.class, rentalRef -> log.info("Bike requested, rentalRef={}", rentalRef))
                      .onError(error -> log.error("Failed to request bike", error));
    }
}
```

## What changed

- Import: AF4 → AF5 FQN on `CommandGateway`. The AF4
  `CommandCallback`, `CommandMessage`, `CommandResultMessage` imports
  are dropped — the SPI does not exist in AF5.
- `.send(cmd, callback)` (AF4 two-arg) →
  `.send(cmd).onSuccess(R.class, payload -> ...).onError(t -> ...)`
  on the `CommandResult`.
- `.onSuccess(R.class, BiConsumer<R, Message>)` is also available if
  the result `Message` itself is needed. Prefer the simpler
  `Consumer<R>` form unless metadata access is required.
- Behavior is preserved: same success branch, same error branch. Do
  **not** silently change error semantics — if the AF4 callback
  rethrew, do the same in `.onError`.
- A class implementing AF4's `CommandCallback` SPI directly (separate
  type, not anonymous) is a refactor: flag for the user; rewrite is
  callsite-specific.
