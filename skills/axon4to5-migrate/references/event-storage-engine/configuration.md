# Configuration Classes

Compact playbook for AF4 configuration classes touched during the
event-storage/configuration phase.

## Canonical reference

- [../../docs/paths/configuration.adoc](../../docs/paths/configuration.adoc)
- [../../docs/paths/event-store.adoc](../../docs/paths/event-store.adoc)

## Goal

Move AF4 bootstrap reads and generic configurer writes to AF5 configuration
APIs without changing the application's wiring style.

## In scope

- Reads from AF4 `Configuration`: `eventStore()`, `eventBus()`,
  `commandBus()`, `queryBus()`, `queryUpdateEmitter()`, token/DLQ lookups.
- Generic write-side config: `ConfigurerModule`, `DefaultConfigurer`,
  lifecycle hooks, `Lifecycle`, generic `registerComponent(...)`.

## Out of scope

- Topic-specific rewrites owned by aggregate/event-processor/gateway recipes.
- Data/schema migration.
- Unsupported AF4 beans whose AF5 successor does not exist yet; comment and
  record them instead.

## Procedure

1. **Classify the class.**

   | Signal | Path |
   |---|---|
   | only reads AF4 root components | read path |
   | declares `ConfigurerModule` / `DefaultConfigurer` / `registerComponent` | write path |
   | both | run read path, then write path |

2. **Read path: replace root lookups.**

   | AF4 read | AF5 direction |
   |---|---|
   | `configuration.eventStore()` / `eventBus()` | inject/read the AF5 `EventStorageEngine`, event store module, or component-specific API required by the caller |
   | `commandBus()` | use AF5 command bus/dispatcher API |
   | `queryBus()` / `queryUpdateEmitter()` | use AF5 query bus/emitter API |
   | token/DLQ/event processor lookup | use event-processing module APIs or route to `event-processor/configuration-reads.md` |

3. **Write path: move configurer shape.**

   | AF4 shape | AF5 shape |
   |---|---|
   | Spring `@Bean ConfigurerModule` for non-Axon components | `@Bean ConfigurationEnhancer` |
   | `DefaultConfigurer.defaultConfiguration()` | focused `MessagingConfigurer` / `EventSourcingConfigurer` |
   | free-standing `onStart` / `onShutdown` | lifecycle registration on AF5 component/configuration APIs |
   | `implements Lifecycle` | component-tied lifecycle hooks |
   | generic `registerComponent(...)` | typed AF5 component registration where available |

4. **Unsupported or deferred writes.**
   - Do not delete AF4 beans with no AF5 replacement.
   - Comment with `TODO[AF5 migration: <blocker-key>]`.
   - Surface the exact blocker key in Output notes.

5. **Verify.**
   - Compile this class and direct collaborators in an isolated scope.
   - If a topic-specific API is needed, route to that topic recipe rather than
     continuing to broaden this file.

## Verify

- No AF4 `Configuration` root read remains unless intentionally blocked.
- No `ConfigurerModule` / `DefaultConfigurer` use remains unless intentionally
  blocked.
- Every commented AF4 surface has a TODO marker and blocker record.
