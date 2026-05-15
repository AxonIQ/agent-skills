package com.example.sequencing;

// AF4 custom SequencingPolicy that derives the sequence id from two metadata keys.
// AF5 form rewires the interface, method signature, accessor names, and return wrapping.

import org.axonframework.eventhandling.EventMessage;
import org.axonframework.eventhandling.async.SequencingPolicy;

public class TenantAndGameSequencingPolicy implements SequencingPolicy<EventMessage<?>> {

    public static final String TENANT_KEY = "tenant-id";
    public static final String GAME_ID_KEY = "game-id";

    @Override
    public Object getSequenceIdentifierFor(EventMessage<?> event) {
        String tenant = (String) event.getMetaData().get(TENANT_KEY);
        String gameId = (String) event.getMetaData().get(GAME_ID_KEY);
        if (tenant == null || gameId == null) {
            return null;
        }
        return tenant + ":" + gameId;
    }
}
