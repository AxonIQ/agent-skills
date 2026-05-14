**Result:** ✅ Success
**Source:** `com.example.sequencing.TenantAndGameSequencingPolicy`
**Recipe:** axon4to5-event-processor

**Notes:**
- Custom `SequencingPolicy` migrated per Step 7 (use-case 06).
- Interface swapped: `org.axonframework.eventhandling.async.SequencingPolicy<EventMessage<?>>` → `org.axonframework.messaging.core.sequencing.SequencingPolicy` (generic parameter dropped — AF5 binds message type at registration).
- `EventMessage` import moved: `org.axonframework.eventhandling.EventMessage` → `org.axonframework.messaging.eventhandling.EventMessage`.
- Added imports: `org.axonframework.messaging.core.ProcessingContext`, `java.util.Optional`.
- Method renamed + signature changed: `Object getSequenceIdentifierFor(EventMessage<?> event)` → `Optional<Object> sequenceIdentifierFor(EventMessage message, ProcessingContext context)`. AF5 `Message` is non-generic — dropped `<?>`.
- Body rewrites: `event.getMetaData()` → `message.metaData()`; `return null;` → `return Optional.empty();`; `return tenant + ":" + gameId;` → `return Optional.of(tenant + ":" + gameId);`.

**Learnings:**
- The projector class that depends on this policy must carry class-level `@SequencingPolicy(type = TenantAndGameSequencingPolicy.class)` (no `parameters` for custom policies). AF4 `assignSequencingPolicy(...)` / YAML `axon.eventhandling.processors.<group>.sequencing-policy` references must be removed (handled by the projector's own recipe run).
- Returning bare `null` from `Optional<Object>` would compile but NPE at scheduler — verified zero `return null` remain.
