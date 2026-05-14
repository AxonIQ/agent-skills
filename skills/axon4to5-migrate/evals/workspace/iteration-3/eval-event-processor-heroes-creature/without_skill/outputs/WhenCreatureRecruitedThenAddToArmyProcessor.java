package com.dddheroes.heroesofddd.creaturerecruitment.automation;

import com.dddheroes.heroesofddd.armies.write.addcreature.AddCreatureToArmy;
import com.dddheroes.heroesofddd.creaturerecruitment.write.changeavailablecreatures.IncreaseAvailableCreatures;
import com.dddheroes.heroesofddd.creaturerecruitment.events.CreatureRecruited;
import com.dddheroes.heroesofddd.shared.application.GameMetaData;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.axonframework.eventhandling.annotations.DisallowReplay;
import org.axonframework.eventhandling.annotations.EventHandler;
import org.axonframework.eventhandling.processors.streaming.sequencing.SequencingPolicy;
import org.axonframework.eventhandling.processors.streaming.sequencing.PropertySequencingPolicy;
import org.axonframework.configuration.annotation.ProcessingGroup;
import org.axonframework.messaging.annotations.MetadataValue;
import org.springframework.stereotype.Component;

import java.util.concurrent.CompletableFuture;

@ProcessingGroup("Automation_WhenCreatureRecruitedThenAddToArmy_Processor")
@DisallowReplay
@SequencingPolicy(type = PropertySequencingPolicy.class, parameters = {GameMetaData.GAME_ID_KEY})
@Component
class WhenCreatureRecruitedThenAddToArmyProcessor {

    @EventHandler
    void react(
            CreatureRecruited event,
            @MetadataValue(GameMetaData.GAME_ID_KEY) String gameId,
            @MetadataValue(GameMetaData.PLAYER_ID_KEY) String playerId,
            CommandGateway commandGateway
    ) {
        var command = AddCreatureToArmy.command(
                event.toArmy(),
                event.creatureId(),
                event.quantity()
        );
        CompletableFuture<?> dispatch = commandGateway.send(command, GameMetaData.with(gameId, playerId), Object.class)
                .exceptionallyCompose(throwable -> {
                    var compensatingAction = IncreaseAvailableCreatures.command(
                            event.dwellingId(),
                            event.creatureId(),
                            event.quantity()
                    );
                    return commandGateway.send(compensatingAction, GameMetaData.with(gameId, playerId), Object.class);
                });
        dispatch.join();
    }
}
