package com.dddheroes.heroesofddd.creaturerecruitment.read.getalldwellings;

import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.messaging.annotation.MetaDataValue;
import org.axonframework.queryhandling.QueryHandler;
import org.springframework.stereotype.Component;

@ProcessingGroup("Read_GetAllDwellings_QueryCache")
@Component
class GetAllDwellingsQueryHandler {

    private final DwellingReadModelRepository dwellingReadModelRepository;

    GetAllDwellingsQueryHandler(DwellingReadModelRepository dwellingReadModelRepository) {
        this.dwellingReadModelRepository = dwellingReadModelRepository;
    }

    @QueryHandler
    GetAllDwellings.Result handle(GetAllDwellings query) {
        var dwellings = dwellingReadModelRepository.findAllByGameId(query.gameId());
        return new GetAllDwellings.Result(dwellings);
    }

    @EventHandler
    void evolve(DwellingBuilt event, @MetaDataValue("gameId") String gameId) {
        var item = new DwellingReadModel(gameId, event.dwellingId(), event.creatureId(), event.costPerTroop(), 0);
        dwellingReadModelRepository.save(item);
    }
}
