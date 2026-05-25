# 02 — Projector with in-handler command dispatch (CommandGateway → CommandDispatcher)

**Why this case is interesting:** "Automation" / process-manager-style projectors that observe events and dispatch commands. AF4 injected `CommandGateway` as a field and called `sendAndWait(...)` in the handler body. AF5 moves the gateway to a method parameter (`CommandDispatcher`), and `sendAndWait` is gone — the future from `send(...).getResultMessage()` surfaces failure off-thread. Try/catch compensation paths become `.exceptionallyCompose(...)`. The handler return type changes from `void` to `CompletableFuture<?>`.

**Apply-condition:** `$SOURCE` injects a `CommandGateway` field AND dispatches commands in `@EventHandler` bodies.

## Before (AF4)

```java
package com.dddheroes.heroesofddd.automation;

import com.dddheroes.heroesofddd.creaturerecruitment.events.CreatureRecruited;
import com.dddheroes.heroesofddd.armies.write.addcreature.AddCreatureToArmy;
import com.dddheroes.heroesofddd.creaturerecruitment.write.changeavailablecreatures.IncreaseAvailableCreatures;
import com.dddheroes.heroesofddd.shared.metadata.GameMetaData;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.DisallowReplay;
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.messaging.MetaData;
import org.axonframework.messaging.annotation.MetaDataValue;
import org.springframework.stereotype.Component;

@Component
@ProcessingGroup("Automation_WhenCreatureRecruitedThenAddToArmy_Processor")
@DisallowReplay
public class WhenCreatureRecruitedThenAddToArmyProcessor {

    private final CommandGateway commandGateway;

    public WhenCreatureRecruitedThenAddToArmyProcessor(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @EventHandler
    public void on(CreatureRecruited event,
                   @MetaDataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        MetaData metadata = GameMetaData.with(gameId);
        try {
            commandGateway.sendAndWait(
                AddCreatureToArmy.command(
                    event.toArmy(), event.creatureId(), event.quantity()
                ),
                metadata
            );
        } catch (Exception failure) {
            // compensation — increase availability back
            commandGateway.sendAndWait(
                IncreaseAvailableCreatures.command(
                    event.dwellingId(), event.creatureId(), event.quantity()
                ),
                metadata
            );
        }
    }
}
```

## After (AF5)

```java
package com.dddheroes.heroesofddd.automation;

import com.dddheroes.heroesofddd.creaturerecruitment.events.CreatureRecruited;
import com.dddheroes.heroesofddd.armies.write.addcreature.AddCreatureToArmy;
import com.dddheroes.heroesofddd.creaturerecruitment.write.changeavailablecreatures.IncreaseAvailableCreatures;
import com.dddheroes.heroesofddd.shared.metadata.GameMetaData;
import org.axonframework.messaging.commandhandling.gateway.CommandDispatcher;
import org.axonframework.messaging.core.Message;
import org.axonframework.messaging.core.Metadata;
import org.axonframework.messaging.core.annotation.MetadataValue;
import org.axonframework.messaging.core.annotation.Namespace;
import org.axonframework.messaging.core.sequencing.MetadataSequencingPolicy;
import org.axonframework.messaging.core.annotation.SequencingPolicy;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay;
import org.springframework.stereotype.Component;

import java.util.concurrent.CompletableFuture;

@Component
@Namespace("Automation_WhenCreatureRecruitedThenAddToArmy_Processor")
@DisallowReplay
@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)
public class WhenCreatureRecruitedThenAddToArmyProcessor {

    @EventHandler
    public CompletableFuture<? extends Message> on(CreatureRecruited event,
                                                   @MetadataValue(GameMetaData.GAME_ID_KEY) String gameId,
                                                   CommandDispatcher commandDispatcher) {
        Metadata metadata = GameMetaData.with(gameId);
        return commandDispatcher.send(
                AddCreatureToArmy.command(
                    event.toArmy(), event.creatureId(), event.quantity()
                ),
                metadata
            )
            .getResultMessage()
            .thenApply(m -> (Message) m)
            .exceptionallyCompose(failure ->
                commandDispatcher.send(
                        IncreaseAvailableCreatures.command(
                            event.dwellingId(), event.creatureId(), event.quantity()
                        ),
                        metadata
                    )
                    .getResultMessage()
                    .thenApply(m -> m)
            );
    }
}
```

## What changed

- `@ProcessingGroup` → `@Namespace` (string preserved).
- `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)` added at class level (AF4 had a `@Bean SequencingPolicy gameIdSequencingPolicy` referenced via `EventProcessingConfigurer.assignSequencingPolicy(...)` for this group — see use-case 03).
- `@DisallowReplay` import: `org.axonframework.eventhandling.DisallowReplay` → `org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay`.
- `@EventHandler` import to AF5 location.
- `@MetaDataValue` → `@MetadataValue` (capital-D loss + package change).
- **Class-level `CommandGateway` field removed.** Constructor injection removed too — the class has no remaining dependencies in this example, so the explicit constructor is also gone.
- Handler method signature gains `CommandDispatcher commandDispatcher` as the **last** parameter. AF5 binds it to the active `ProcessingContext` automatically.
- Handler return type: `void` → `CompletableFuture<? extends Message>`. AF5 `Message` is NON-generic — `CompletableFuture<? extends Message<?>>` (with the `<?>`) does NOT compile.
- `sendAndWait(...)` → `send(...).getResultMessage()` — returns `CompletableFuture<? extends Message>`. The AF4 blocking semantics are replaced with the async chain.
- Try/catch compensation → `.exceptionallyCompose(failure -> commandDispatcher.send(<compensation>).getResultMessage())`. The `.thenApply(m -> m)` bridge widens the wildcard capture so the future type lines up with what `exceptionallyCompose` expects.

## Caveats

- **`sendAndWait` is not just an API rename.** The AF4 form blocked + threw on failure. The AF5 form returns a `CompletableFuture` and the failure surfaces on the future, NOT in the try-block. AF4 try/catch around `sendAndWait` silently stops compensating under AF5 if you "just remove the await" — that is a real behavioural regression. Always rewrite compensation to `.exceptionallyCompose(...)`.
- **AF5 `Message` is non-generic.** Declared as `public interface Message` (no type parameter). Anything that writes `Message<?>` in the wildcard position fails to compile against AF5. The correct shape is `CompletableFuture<? extends Message>`.
- **`.thenApply(m -> m)` bridge** is often needed before `.exceptionallyCompose(...)` to widen `CompletableFuture<? extends Message>` to `CompletableFuture<Message>` (wildcard capture refuses `exceptionallyCompose`'s type bound otherwise).
- **`CommandDispatcher` is bound to `ProcessingContext`**, NOT to a bean lifecycle. Do not keep a class-level field side-by-side with the parameter — that mixes two dispatch paths and confuses readers.
- **Helper methods that build metadata (e.g. `GameMetaData.with(gameId)`) often return AF4 `org.axonframework.messaging.MetaData`.** If they don't get migrated to AF5 `org.axonframework.messaging.core.Metadata`, command dispatch fails at runtime (type-check passes due to similarity). Flag in Result NOTES; the helper migration is outside the strict event-processor recipe scope.
- **`@DisallowReplay` semantics unchanged** — it still means "skip this handler during a reset/replay". Only the import location moves.
