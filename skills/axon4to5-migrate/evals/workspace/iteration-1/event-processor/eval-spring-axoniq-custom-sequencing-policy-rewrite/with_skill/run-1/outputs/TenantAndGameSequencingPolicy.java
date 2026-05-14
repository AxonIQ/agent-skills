package com.example.sequencing;

// AF4 custom SequencingPolicy that derives the sequence id from two metadata keys.
// AF5 form rewires the interface, method signature, accessor names, and return wrapping.

import org.axonframework.messaging.core.ProcessingContext;
import org.axonframework.messaging.core.sequencing.SequencingPolicy;
import org.axonframework.messaging.eventhandling.EventMessage;

import java.util.Optional;

public class TenantAndGameSequencingPolicy implements SequencingPolicy {

    public static final String TENANT_KEY = "tenant-id";
    public static final String GAME_ID_KEY = "game-id";

    @Override
    public Optional<Object> sequenceIdentifierFor(EventMessage message, ProcessingContext context) {
        String tenant = (String) message.metaData().get(TENANT_KEY);
        String gameId = (String) message.metaData().get(GAME_ID_KEY);
        if (tenant == null || gameId == null) {
            return Optional.empty();
        }
        return Optional.of(tenant + ":" + gameId);
    }
}
