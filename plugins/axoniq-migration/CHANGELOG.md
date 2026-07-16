# Changelog

All notable changes to the **axoniq-migration** plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
