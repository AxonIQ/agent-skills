package com.dddheroes.heroesofddd.creaturerecruitment.read;

import com.dddheroes.heroesofddd.creaturerecruitment.events.DwellingBuilt;
import com.dddheroes.heroesofddd.creaturerecruitment.events.AvailableCreaturesChanged;
import com.dddheroes.heroesofddd.creaturerecruitment.events.CreatureRecruited;
import com.dddheroes.heroesofddd.shared.application.GameMetaData;
import org.axonframework.eventhandling.annotations.EventHandler;
import org.axonframework.eventhandling.processors.streaming.sequencing.SequencingPolicy;
import org.axonframework.eventhandling.processors.streaming.sequencing.annotations.SequencingPolicy;
import org.axonframework.eventhandling.processors.ResetHandler;
import org.axonframework.eventstreaming.annotations.ProcessingGroup;
import org.axonframework.messaging.annotations.MetadataValue;
import org.springframework.stereotype.Component;

@ProcessingGroup("ReadModel_Dwelling")
@SequencingPolicy(metadataKey = GameMetaData.GAME_ID_KEY)
@Component
class DwellingReadModelProjector {

    private final DwellingReadModelRepository repository;

    DwellingReadModelProjector(DwellingReadModelRepository repository) {
        this.repository = repository;
    }

    @EventHandler
    void on(DwellingBuilt event, @MetadataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        var state = new DwellingReadModel(
                gameId,
                event.dwellingId(),
                event.creatureId(),
                event.costPerTroop(),
                0
        );
        repository.save(state);
    }

    @EventHandler
    void on(AvailableCreaturesChanged event) {
        repository.findById(event.dwellingId())
                  .map(state -> state.withAvailableCreatures(event.changedTo()))
                  .ifPresent(repository::save);
    }

    @EventHandler
    void on(CreatureRecruited event) {
        repository.findById(event.dwellingId())
                  .map(state -> state.withAvailableCreaturesDecreasedBy(event.quantity()))
                  .ifPresent(repository::save);
    }

    @ResetHandler
    void onReset() {
        repository.deleteAll();
    }
}
