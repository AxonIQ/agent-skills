# Changelog

All notable changes to the **axoniq-migration** plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- `axon4to5-migrate-code`: **added `axon-legacy` as the recommended saga strategy, alongside the existing JPA-state rewrite.** AF5 ports `@Saga`, `@SagaEventHandler`, `@StartSaga`, `@EndSaga`, `SagaLifecycle`, `AssociationValue` and every `SagaStore` implementation into `org.axonframework:axon-legacy` under their AF4 package names, so a saga can keep running as-is with its existing store rows. The recipe still opens with the Blocker B0 strategy decision, now between **`axon-legacy`** and the pre-existing **`stateful-rewrite`** (rebuild as a `@Component @DisallowReplay` handler over a new JPA state entity + repository). `axon-legacy` is marked `(Recommended)` unconditionally, so `auto=true` always takes it: it is the only strategy that lets unfinished AF4 instances finish, the only one that keeps the application starting new instances, and the only place framework deadlines can ever come from, while `stateful-rewrite` silently abandons the saga-store rows. `stateful-rewrite` is the right pick only when nothing unfinished has to run in the app, the AF5 application just starts new processes, and timeouts will be hand-built. Under `axon-legacy` the recipe verifies the OpenRewrite `Axon4ToAxon5Legacy` pass (static `SagaLifecycle` -> handler parameter; `CommandGateway` field -> `CommandDispatcher` parameter, `sendAndWait` -> `FutureUtils.joinAndUnwrap(...)`) and closes the gaps that pass cannot: remaining field-injected collaborators -> handler parameters (AF5 has no `ResourceInjector`), synchronous handlers, processor-name preservation through `@ProcessingGroup` -> `@Namespace`, and `Sagas.of(...)` wiring for `configuration=native`. Two `axon-legacy`-only blockers: **B1** deadlines (not ported, upstream #5006; recommends `skip` so `auto=true` never silently disables a live timeout -- under `stateful-rewrite` hand-built timeouts are the accepted premise, so it is not a blocker there) and **B2** an undeterminable AF4 processor name (renaming it strands in-flight sagas on a token the store cannot find). Six use cases, grouped by strategy: legacy Spring Boot, legacy native `Sagas.of(...)`, legacy deadline blocker, rewrite JPA state, rewrite deadline comment-out, rejected-not-a-saga.
- `axon4to5-openrewrite`: documented that the recipe adds `org.axonframework:axon-legacy` to any module using saga types, and what its `Axon4ToAxon5Legacy` sub-recipe rewrites. A new `axon-legacy` dependency in the diff is expected output, not a defect. Noted that the sub-recipe ships from `axon-migration` 5.4.0 onward, so on an older pinned `references/recipe-version` the saga recipe applies the same rewrites by hand.
- `axon4to5-migrate-code`: `SagaTestFixture` is no longer a blocker. `axon-legacy-test` ports it under its AF4 package `org.axonframework.test.saga`, so an existing saga test keeps its fixture and its given-when-then API instead of being rewritten to `AxonTestFixture`. Two caveats the saga recipe now enforces: the fixture runs a started `AxonConfiguration` holding a live event processor and implements `AutoCloseable`, so **every** test class constructing one needs an `@AfterEach` calling `close()` (it compiles and passes without one, leaving the processor running); and its deadline / event-scheduler methods throw `UnsupportedOperationException` until deadlines land. The aggregate recipe's blocker B2 was dropped and B3 renumbered to B2.

### Fixed

- `axon4to5-migrate-code`: preserve command routing when migrating `@TargetAggregateIdentifier`. AF4's `@TargetAggregateIdentifier` was both the target-id and the command's routing key (same-entity commands handled sequentially); migrating it to `@TargetEntityId` alone drops that guarantee. The pinned OpenRewrite recipe (5.2.0) now lifts `routingKey` automatically in the common case (AxonIQ/AxonFramework#4701); the aggregate recipe verifies the result and reconciles `@Command(routingKey = "…")` against the command's actual state (absent / bare / already correct) as a safety net, covering Kotlin `data class` properties too. Docs and use-case examples updated accordingly.

## [0.2.2] - 2026-07-19

### Fixed

- Removed all `-SNAPSHOT` / Sonatype snapshots references — the Axoniq/Axon Framework 5 binaries and the `org.axonframework:axon-migration` recipe artifact are released on Maven Central (current `5.2.0`), so a migration run no longer gets confused about availability:
  - `axon4to5-openrewrite`: pinned recipe version 5.1.1 → **5.2.0** (`references/recipe-version`); `assets/init.gradle` default `axonMigrationVersion` → 5.2.0 and dropped the unconditional Sonatype snapshots + `mavenLocal` repositories (Maven Central only); failure-routing text no longer lists Sonatype snapshots as a repository.
  - `axon4to5-migrate-code`: bumped the target-release example in `openrewrite-code-conversion.adoc` to 5.2.0; removed `-SNAPSHOT` from the `axon-messaging` jar reference in `FLOW.md` and from the "verified against" provenance notes in the aggregate/snapshotting recipe files (5.1.2-SNAPSHOT → 5.1.2).
- `axon4to5-migrate-code`: refreshed now-outdated "coming in 5.2.0" reference-doc content now that 5.2.0 is released — `docs/paths/index.adoc` reframes the annotated timeouts/interceptors/exception-handling features as delivered (with the real `@CommandHandlerInterceptor`/`@EventHandlerInterceptor`/`@QueryHandlerInterceptor` names) and replaces the "event upcasting not yet available" note with the 5.2.0 message-transformation successor; `docs/paths/interceptors.adoc` documents the shipped annotated-interceptor contract instead of "will be functional in 5.2.0". The "Multiple Event Sources not yet available" note is likewise corrected: `MultiStreamableEventSource` ships in the commercial `io.axoniq.framework:axoniq-event-streaming` module (on Maven Central since 5.1.0). Event replaying is corrected from "not yet implemented" to available in the core framework (`StreamingEventProcessor.resetTokens()`, `@ResetHandler`, `ReplayToken`/`@ReplayContext`, `EventTrackerStatus.isReplaying()`); the Saga & Deadline note now states plainly they are unavailable in AF5 with their future still being decided (rather than "redesign in progress").

## [0.2.1] - 2026-07-16

### Changed

- `axon4to5-migrate-code`: updated the interceptors recipe's B1 blocker (`@MessageHandlerInterceptor` as method annotation) for the Axon Framework 5.2.0 release — the annotation form is now supported on 5.2.0+ (as `@CommandHandlerInterceptor` / `@EventHandlerInterceptor` / `@QueryHandlerInterceptor` with a changed method contract); the blocker text now presents that as a concrete manual resolution instead of "wait for 5.2.0". The recipe still does not automate that rewrite.
- `axon4to5-migrate-code`: the serializer recipe's `@Revision`/upcasting Learning note now points at the 5.2.0 upcaster successor (message transformation, `io.axoniq.framework:axoniq-message-transformation`).

## [0.2.0] - 2026-06-04

### Changed

- Renamed the `axon4to5-migrate` skill to **`axon4to5-migrate-code`** (directory and skill `name`); updated the cross-reference in `axon4to5-isolatedtest` and the skill listings in the repo `README.md` and `DEVELOPMENT.md`.
- Clarified the skill's scope: it migrates **code and configuration only** and does **not** migrate stored data (event store contents / stored events, tracking tokens), which are left untouched. Updated the skill `description` and Goal section accordingly.

## [0.1.0] - 2026-06-02

### Added

- Initial release of the Axon Framework 4 → 5 / Axoniq Framework 5 migration plugin, packaged for Claude, Codex, and Cursor under the `axoniq` marketplace. Bundles three skills:
  - **`axon4to5-migrate`** — phased migration orchestrator (single-element or whole-project; inline or sub-agent execution) with a recipe library for aggregates, command/query gateways and handlers, event processors, the event store, interceptors, sagas, and serializers, plus a durability state machine.
  - **`axon4to5-openrewrite`** — applies the Axon 4 → 5 OpenRewrite bulk-migration recipe (Maven or Gradle, free or commercial variant); detects the build tool, runs, and offers to commit. Idempotent.
  - **`axon4to5-isolatedtest`** — internal helper that scopes a Maven/Gradle compile+test to one target class via a per-target profile or source-set.
