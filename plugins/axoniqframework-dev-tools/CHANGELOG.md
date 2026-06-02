# Changelog

All notable changes to the **axoniqframework-dev-tools** plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> History before 0.3.9 was authored upstream while this plugin was named `axoniq-claude-plugin`;
> entry bodies are preserved verbatim and only the version headers were normalized.

## [0.3.9] - 2026-06-02

### Changed

- Renamed from `axoniq-claude-plugin` to **`axoniqframework-dev-tools`** and folded into the `axoniq` multi-runtime marketplace; now packaged for Claude, Codex, and Cursor. No skill-content changes.

## [0.3.8] - 2026-06-01

### Added

- `SKILL.md`: pointer to the published Javadoc at **apidocs.axoniq.io** for investigating any API the guides don't document. Notes the version-by-minor URL scheme (a version `x.y.z` lives under the `x.y` segment, e.g. `apidocs.axoniq.io/5.1/`) and that it covers both `org.axonframework` and `io.axoniq.framework` packages.

## [0.3.7] - 2026-06-01

### Added

- `getting-started/dependencies.md`: new **"Which BOM should I use?"** section giving an explicit decision rule between `org.axonframework:axon-framework-bom` (open-source only) and `io.axoniq.framework:axoniq-framework-bom` (any commercial Axoniq module). Clarifies that the Axoniq BOM is a version-managing superset, imports the AF5 BOM transitively, and on its own pulls in no commercial code or licensing obligation.

## [0.3.6] - 2026-06-01

### Changed

- Normalized brand capitalization in prose from "AxonIQ" to **"Axoniq"** across the skill guides and the contributor docs-update conventions (e.g. "Axoniq Framework", "Axoniq Platform"). Code identifiers, `io.axoniq` groupIds, GitHub URLs, and the `AxonIQ/AxonFramework` repo slug are unchanged.

## [0.3.5] - 2026-06-01

### Added

- **New `foundations/message-streams.md` guide** documenting the `MessageStream` API (verified against the `axon-5.1.1` source): the `Entry<M>` wrapper (`message()`/`getResource`/`withResource`), static factories and their `Single`/`Empty` return subtypes, consumption (`reduce`, `first()`, `Single.asCompletableFuture()`, imperative `next`/`peek`), and transforms. Wired into `SKILL.md` routing and quick-orientation.

### Fixed

- `event-store/primitives.md`: replaced the non-existent `MessageStream.collect(...)` call with a `reduce`-based `ConsistencyMarker` extraction, and clarified that `source(...)` returns a pull-based `MessageStream` (not a `Flux`).
- `queries/query-handling.md`: documented the `subscriptionQuery` `mapper`/`updateBufferSize` overloads with the correct `Function<QueryResponseMessage, R>` mapper type, and clarified that AF5 has no `SubscriptionQueryResult` wrapper.

## [0.3.4] - 2026-05-31

### Added

- Documented Axon Server connection configuration and the `axon.axonserver.enabled` testing gap.

## [0.3.3] - 2026-05-31

### Fixed

- Corrected the Axon Server connector coordinate to `io.axoniq.framework:axon-server-connector`.

## [0.3.2] - 2026-05-31

### Changed

- Recommend an explicit, reverse-DNS namespace on message annotations.

## [0.3.1] - 2026-05-31

### Changed

- **Retarget the `axonframework` skill to the Axon Framework 5.1.x line** (latest stable `5.1.1`):
  - Added a **Target version** anchor near the top of `SKILL.md` so the assumed package layout and feature availability are explicit.
  - `getting-started/dependencies.md`: bumped the pinned version and all BOM coordinates `5.0.4` → `5.1.1`.
  - `events/processors.md`: replay/reset is now described as available **from 5.1** (previously "for reference / not in 5.0").

### Fixed

- **`@Namespace` is available since AF5.1** — corrected guides that still claimed it does not exist (a leftover from the 5.0 target):
  - `configuration/spring-boot.md`: documented `@Namespace` and the `pooledStreamingMatching(name)` / `subscribingMatching(name)` selectors for assigning handlers to processors by namespace; kept the manual package/bean-name selector as the AF5.0 fallback.
  - `foundations/annotations.md`: clarified `@Query(namespace=...)` (single-message `QualifiedName` namespace) vs the separate `@Namespace` annotation (type/package/module-wide, since 5.1).
- **`queries/query-handling.md`**: added the missing `import org.axonframework.messaging.queryhandling.gateway.QueryGateway;` and named the package in prose, matching how the command side documents `CommandGateway`. (The gateway *packages* were already correct — this only adds the previously-omitted import.)
- **`events/versioning-upcasting.md`**: generalized the "not available in 5.0" notes to "through 5.1" (upcasting is still not shipped at 5.1.1; scheduled for 5.2.0).

## [0.3.0] - 2026-05-31

### Added

- **`axonframework` skill — 14 new AF5 open-source guides** filling reference-guide coverage gaps. Each is grounded in the AF5 reference docs and verified against the `axon-5` source tree (APIs that could not be located in source were omitted rather than guessed):
  - `commands/entities.md` — event-sourced entities: `@EventSourcedEntity`, `@EntityCreator`, `@InjectEntity`, hierarchies, polymorphism
  - `commands/dispatching.md` — `CommandGateway`/`CommandBus`, routing keys, command results
  - `events/processors.md` — subscribing vs pooled-streaming processors, tracking tokens, segments, multi-node, reset
  - `events/publishing.md` — `EventAppender` vs `EventGateway`, unit-of-work publication
  - `events/versioning-upcasting.md` — event revisions and conversion-at-handling (upcasting noted as forward-looking / not in 5.0)
  - `event-store/internals.md` — `EventStore`/`EventStorageEngine` layer and storage engines
  - `event-store/conversion-serialization.md` — `Converter` layering, Jackson 3 / Jackson 2 / Avro / CBOR, content types
  - `foundations/messages-and-processing-context.md` — message anatomy, `ProcessingContext`/unit-of-work lifecycle, correlation
  - `foundations/exception-handling.md` — `@ExceptionHandler`, execution-exception wrapping, handler timeouts (timeouts flagged provisional for 5.2.0)
  - `foundations/supported-parameters.md` — reference of injectable handler parameters
  - `foundations/handler-customization.md` — custom `ParameterResolver`/`HandlerEnhancerDefinition`, meta-annotations
  - `foundations/identifiers.md` — `IdentifierFactory` and custom identifier generation
  - `testing/advanced.md` — time control, integration tests, Spring Boot test setup
  - `testing/matchers.md` — matcher API and field filters

### Fixed

- **`testing/basics.md`** corrected against the real AF5 test API (mismatches surfaced while authoring the new testing guides):
  - removed the non-existent `Customization.disableAxonServer()` — heavy infrastructure (Axon Server) is excluded by default; opt into it with `asIntegrationTest()`
  - `eventsMatch(...)`/`commandsMatch(...)` take a `Predicate`, not a Hamcrest `Matcher` — the matcher example now uses the `eventsSatisfy(...)` form
  - clarified that `exception(type, message)` compares the message with `String.equals` (exact), not a substring
- **`commands/decision-models-dcb.md`** — removed the same non-existent `disableAxonServer()` fixture call.
- **`production-infra/multi-source-streaming.md`** — `EventMessage.getTimestamp()` → `timestamp()` (AF5 has no `get`-prefixed accessor).
- **Independent QA sweep of the 14 new guides** — each re-verified against `axon-5` source by a reviewer that did not author it; the following real defects were corrected:
  - `commands/dispatching.md` — `messagingConfigurer(...)` is not a real method (→ `componentRegistry(cr -> cr.registerComponent(...))`); `registerCommandBus` is on `MessagingConfigurer` (→ `messaging(mc -> mc.registerCommandBus(...))`)
  - `events/processors.md` — `customize(...)` → `customized(...)`; dropped the non-existent `load-balancing-strategy` property; `thenApply` → `thenCompose` for chained async resets; corrected the replay cross-reference (`ReplayStatus`/`@ReplayContext` are not documented in `handling-projections.md`)
  - `foundations/messages-and-processing-context.md` — `@EventHandler(messageType = ...)` is not a real attribute (→ `eventName` + `payloadType`)
  - `foundations/supported-parameters.md` — `@InjectEntity` resolves the id from the payload's `@TargetEntityId` by default (not "the command's routing key"); corrected the message-subtype package column
  - `foundations/handler-customization.md` — fixed a broken `plain-java.md` link (→ `../configuration/plain-java.md`); softened an inaccurate `TracingHandlerEnhancerDefinition` citation
  - `commands/entities.md` — replaced the fabricated `BroadcastToAllChildrenMatcher` with a clearly user-supplied `EventTargetMatcherDefinition`
  - `events/versioning-upcasting.md`, `events/publishing.md`, `event-store/internals.md`, `foundations/exception-handling.md`, `foundations/identifiers.md`, `testing/matchers.md` — verified clean
  - `event-store/conversion-serialization.md` — re-pointed the "how events change shape over time" cross-reference to `events/versioning-upcasting.md`
  - `testing/advanced.md` — `EventMessage.getTimestamp()` → `timestamp()`; corrected the Spring `axon.axonserver.enabled` "absent" semantics; added the `@ExtendWith`/`@ProvidedAxonTestFixture` test-class wiring snippet

### Changed

- **`axonframework` skill — guide reorganization.** Regrouped the 13 flat guide folders into domain folders that mirror the AF5 reference guide. No content changes; renames only, with all cross-references and the `SKILL.md` routing table updated:
  - `dependencies/guide.md` → `getting-started/dependencies.md`
  - `message-annotations/guide.md` → `foundations/annotations.md`, `interceptors/guide.md` → `foundations/interceptors.md`
  - `command-handling/guide.md` → `commands/stateless.md`, `command-decision-models/guide.md` → `commands/decision-models-dcb.md`
  - `event-handling/guide.md` → `events/handling-projections.md`
  - `query-handling/guide.md` → `queries/query-handling.md`
  - `event-store-primitives/guide.md` → `event-store/primitives.md`
  - `configuration/guide.md` → `configuration/plain-java.md`, `spring-configuration/guide.md` → `configuration/spring-boot.md`
  - `testing/guide.md` → `testing/basics.md`
  - `distributed-messaging/guide.md` → `production-infra/distributed-messaging.md`, `event-streaming/guide.md` → `production-infra/multi-source-streaming.md`

## [0.2.0] - 2026-04-18

### Added

- **`message-annotations/guide.md`** — complete reference for every AF5 annotation with all attributes, imports, and examples: `@Command`, `@Event`, `@Query`, `@CommandHandler`, `@EventHandler`, `@QueryHandler`, `@InjectEntity`, `@EventSourcedEntity`, `@EventTag`, `@EntityCreator`, `@ExceptionHandler`, `@DisallowReplay`, and injectable parameter types
- **`dependencies/guide.md`** — Maven and Gradle coordinates, current versions, and module purposes for both Axon Framework 5 (`org.axonframework`, latest stable `5.0.4`) and AxonIQ Framework (`io.axoniq.framework`); BOM usage, typical setups, and transitive dependency tree
- **`spring-configuration/guide.md`** — Spring Boot auto-detection rules (`MessageHandlerLookup`, `SpringEventSourcedEntityLookup`), `@EventSourced` stereotype with all attributes, `@Namespace` for processor routing, full `EventProcessorDefinition` fluent API, `PooledStreamingEventProcessorConfiguration` and `SubscribingEventProcessorConfiguration` method references, and `application.yml` processor properties
- **`configuration/guide.md`** — completely rewritten to cover the configurer hierarchy (`MessagingConfigurer` → `ModellingConfigurer` → `EventSourcingConfigurer`), full API reference with shorthand vs low-level equivalents, event processing configuration, transaction management, and event store backends

### Fixed

- `command-handling/guide.md`: registration example used a non-existent `.commands()` method — corrected to `registerCommandHandlingModule()` with `autodetectedCommandHandlingComponent()`; added `@Command(routingKey)` section for distributed routing and `@InjectEntity` resolution
- `testing/guide.md`: seeding section was documenting `GenericTaggedEventMessage` as the correct way to seed tagged events for `@InjectEntity` tests — this is wrong because `TaggedEventMessage<E>` does not extend `EventMessage`, causing the fixture to treat the tagged message as an opaque payload and discard all tags silently; corrected to use plain event payloads (tags are resolved automatically via `AnnotationBasedTagResolver`); added explicit pitfall warning with explanation of root cause
- `SKILL.md` routing table updated with all four new guides and matching quick-orientation entries
