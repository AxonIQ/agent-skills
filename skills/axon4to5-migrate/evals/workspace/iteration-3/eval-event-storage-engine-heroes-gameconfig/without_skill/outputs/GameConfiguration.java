package com.dddheroes.heroesofddd;

import com.dddheroes.heroesofddd.shared.application.GameMetaData;
import org.axonframework.eventhandling.EventMessage;
import org.axonframework.eventhandling.sequencing.SequencingPolicy;
import org.axonframework.messaging.correlation.CorrelationDataProvider;
import org.axonframework.messaging.correlation.MessageOriginProvider;
import org.axonframework.messaging.correlation.SimpleCorrelationDataProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.Optional;

@Configuration
public class GameConfiguration {

    @Bean
    public SequencingPolicy gameIdSequencingPolicy() {
        return (EventMessage<?> e) -> Optional.ofNullable(e.getMetaData().get(GameMetaData.GAME_ID_KEY));
    }

    @Bean
    public CorrelationDataProvider gameDataProvider() {
        return new SimpleCorrelationDataProvider(GameMetaData.GAME_ID_KEY, GameMetaData.PLAYER_ID_KEY);
    }

    @Bean
    public CorrelationDataProvider messageOriginProvider() {
        return new MessageOriginProvider();
    }
}
