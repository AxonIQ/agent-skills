package com.example.tokenstore;

// AF4 projector wired to MongoTokenStore via the (now end-of-life) axon-mongo extension.
// AF5 has no axon-mongo release → Blocker B1 fires.

import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.extensions.mongo.eventhandling.tokenstore.MongoTokenStore;
import org.springframework.stereotype.Component;

@Component
@ProcessingGroup("MongoBackedProjector")
public class MongoTokenStoreProjector {

    private final MongoTokenStore tokenStore;
    private final TenantRepository repository;

    public MongoTokenStoreProjector(MongoTokenStore tokenStore, TenantRepository repository) {
        this.tokenStore = tokenStore;
        this.repository = repository;
    }

    @EventHandler
    public void on(TenantCreated event) {
        repository.save(new TenantView(event.tenantId(), event.name()));
    }

    public record TenantCreated(String tenantId, String name) {}
}
