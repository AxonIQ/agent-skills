# Changelog

All notable changes to the **axon4to5** plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-02

### Added

- Initial release of the Axon Framework 4 → 5 / Axoniq Framework 5 migration plugin, packaged for Claude, Codex, and Cursor under the `axoniq` marketplace. Bundles three skills:
  - **`axon4to5-migrate`** — phased migration orchestrator (single-element or whole-project; inline or sub-agent execution) with a recipe library for aggregates, command/query gateways and handlers, event processors, the event store, interceptors, sagas, and serializers, plus a durability state machine.
  - **`axon4to5-openrewrite`** — applies the Axon 4 → 5 OpenRewrite bulk-migration recipe (Maven or Gradle, free or commercial variant); detects the build tool, runs, and offers to commit. Idempotent.
  - **`axon4to5-isolatedtest`** — internal helper that scopes a Maven/Gradle compile+test to one target class via a per-target profile or source-set.
