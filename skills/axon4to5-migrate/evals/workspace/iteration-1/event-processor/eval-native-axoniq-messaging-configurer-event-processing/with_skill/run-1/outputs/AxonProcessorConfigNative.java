package com.example.config;

// AF5 non-Spring bootstrap that wires a pooled streaming processor via MessagingConfigurer.eventProcessing(...).
// See use-case 05 (native-configurer-event-processing).

import org.axonframework.eventsourcing.configuration.EventSourcingConfigurer;
import org.axonframework.messaging.configuration.MessagingConfigurer;

public class AxonProcessorConfigNative {

    public static void main(String[] args) {
        EventSourcingConfigurer eventSourcing = EventSourcingConfigurer.create();

        eventSourcing.messaging(messaging ->
            messaging.eventProcessing(eventProcessing ->
                eventProcessing.pooledStreaming(pooledStreaming ->
                    pooledStreaming.processor("ReadModel_Dwelling", module ->
                        module.eventHandlingComponents(components ->
                                  components.autodetected(cfg ->
                                      new DwellingReadModelProjector(
                                          cfg.getComponent(DwellingReadModelRepository.class)
                                      )
                                  )
                              )
                              .customized((cfg, conf) -> conf.batchSize(100).initialSegmentCount(8))
                    )
                )
            )
        );

        eventSourcing.start();
    }
}
