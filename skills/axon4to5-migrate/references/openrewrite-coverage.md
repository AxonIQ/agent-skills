# OpenRewrite coverage map

Per-pattern breakdown of what the OpenRewrite bulk recipe rewrites versus what the AI must still do
after OR finishes. Each pattern file's `Notes` section also carries an `OpenRewrite status:` line —
this map is the cross-pattern overview.

Coverage values:

- **Full** — OR finishes the pattern with no AI follow-up.
- **Partial** — OR rewrites part; AI fills the documented gap.
- **None** — no OR rule; AI does it from scratch.

| Pattern (file) | OR coverage | What AI still does |
|---|---|---|
| 10-dependencies/maven-gradle-migration.md | Partial | OR renames BOM, bumps versions, renames `axon.serializer` → `axon.converter`, swaps starter to commercial; AI removes `console-framework-client-spring-boot-starter`. |
| 10-dependencies/serializer-to-converter.md | Partial | OR moves the `serialization` → `conversion` package and renames the YAML key prefix; AI renames concrete class names (`JacksonSerializer` → `JacksonConverter`) and fixes `SerializerType.XSTREAM`/`JAVA` enum values. |
| 20-aggregates/aggregate-class.md | Partial | OR rewrites `@Aggregate` → `@EventSourced(tagKey, idType = Object.class)`; AI replaces the `Object.class` placeholder with the real id type. |
| 20-aggregates/aggregate-lifecycle.md | Full | `ReplaceAggregateLifecycleApply` rewrites `apply(...)` → `eventAppender.append(...)` and injects `EventAppender`; AI verifies only. |
| 20-aggregates/aggregate-member.md | Full | `ChangeType` `@AggregateMember` → `@EntityMember`; `routingKey` preserved. |
| 20-aggregates/command-annotation.md | Full | `AddCommandAnnotation` adds `@Command` to command payload types and migrates `@RoutingKey` fields to the `routingKey` attribute. |
| 20-aggregates/command-handler.md | Partial | `ChangeType` moves the import; `EventAppender` param added only on handlers that called `apply(...)` — AI adds it to remaining handlers. |
| 20-aggregates/creation-policy.md | Partial | `RemoveAnnotation` strips `@CreationPolicy`; `ConvertCommandHandlerConstructorToStaticMethod` handles constructor handlers — AI converts remaining ALWAYS handlers to static factories and reviews CREATE_IF_MISSING semantics. |
| 20-aggregates/entity-creator.md | Full | `AddEntityCreatorAnnotation` annotates no-arg constructors. |
| 20-aggregates/event-annotation.md | Full | `AddEventAnnotation` adds `@Event` and migrates `@Revision`; `AddEventTagAnnotation` adds `@EventTag` to event fields. |
| 20-aggregates/event-emission.md | Full | Same `ReplaceAggregateLifecycleApply` recipe as aggregate-lifecycle. |
| 20-aggregates/event-sourcing-handler.md | Full | `ChangeType` for the `@EventSourcingHandler` package move. |
| 20-aggregates/generic-domain-event-message.md | None | No OR rule; AI rewrites `GenericDomainEventMessage` → `GenericEventMessage`. |
| 20-aggregates/target-aggregate-identifier.md | Partial | OR renames `@TargetAggregateIdentifier` → `@TargetEntityId` (keeps the annotation); AI removes it entirely per AF5 routing-by-`idType`. |
| 30-event-handlers/command-dispatcher.md | Partial | `MigrateCommandGatewayInEventHandler` rewrites single-dispatch and try/catch handler bodies; AI handles compound shapes (loops, multiple sequential dispatches). |
| 30-event-handlers/command-gateway-top-level.md | Partial | `ChangePackage` moves the `CommandGateway` import to the `.messaging.` path; AI rewrites the `.send()`/`.sendAndWait()` chains (insert `.resultAs(Type.class)`; replace `.sendAndWait` with `.send().resultAs().orTimeout().join()`). |
| 30-event-handlers/event-bus-to-sink.md | Full | `ChangeType` `EventBus` → `EventSink` (after the upstream `eventhandling` → `messaging.eventhandling` package move). |
| 30-event-handlers/event-handler-annotation.md | Full | `ChangeType` for `@EventHandler`, `@DisallowReplay`, `@ResetHandler` package moves. |
| 30-event-handlers/message-accessors.md | Full | `ChangeMethodName` rewrites `getPayload`/`getMetaData`/`getIdentifier`/`getTimestamp`/`getPayloadType`. |
| 30-event-handlers/metadata-type.md | Full | `ChangeType` `MetaData` → `Metadata`. |
| 30-event-handlers/metadata-value.md | Full | `ChangeType` `@MetaDataValue` → `@MetadataValue`. |
| 30-event-handlers/namespace-routing.md | Full | `ChangeType` `@ProcessingGroup` → `@Namespace`. |
| 30-event-handlers/sequencing-policy.md | Partial | OR moves package, `MigrateSequencingPolicyLambda` rewrites lambdas, `AnnotateObsoleteSequencingPolicyProperty` flags YAML; AI moves YAML wiring onto `@SequencingPolicy` class annotation. |
| 40-query-handlers/query-handler.md | Full | `ChangeType` for `@QueryHandler` package move. |
| 40-query-handlers/query-named.md | None | No OR rule; AI introduces the `@Query` payload record. |
| 40-query-handlers/query-response-types.md | Partial | `Axon4ToAxon5QueryResponseTypes` rewrites the 2-argument typed-payload form and prunes the `responsetypes` import; AI handles the 3-argument named-query form, `multipleInstancesOf` → `queryMany`, and `ResponseType<R>`-typed declarations. |
| 40-query-handlers/query-update-emitter.md | Partial | `ChangePackage` moves `QueryUpdateEmitter`; AI converts constructor field → method param and adds the `Class<Q>` arg to `emit(...)`. |
| 50-interceptors/message-dispatch-interceptor.md | Partial | `MigrateMessageInterceptorSignatures` rewrites the signature; AI rewrites the body (UoW hooks, chain call with arguments). |
| 50-interceptors/message-handler-interceptor.md | Partial | `MigrateMessageInterceptorSignatures` rewrites the signature; AI rewrites the body (UoW hooks → `ProcessingContext`, `chain.proceed()` → `chain.proceed(message, context)`). |
| 60-sagas/saga-component.md | None | No OR rule; AI does the full `@Saga` → `@Component + @Entity` JPA rewrite. |
| 70-event-store/event-store-jpa.md | None | No OR rule; AI writes the `EventStoreConfiguration` bean from scratch. |
| 80-tests/test-fixture.md | Partial | OR renames type, rewrites the fluent DSL, regenerates setup, adds Java `@AfterEach`; AI handles Kotlin tear-down, fills setup the recipe could not infer (raw `new AxonTestFixture(...)`), and replaces `AggregateNotFoundException` with the domain exception. |
