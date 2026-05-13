# Event-Processor Configuration Reads

Use when code directly reads AF4 event-processing components from Axon
`Configuration`.

## Canonical reference

- [../../docs/paths/projectors-event-processors.adoc](../../docs/paths/projectors-event-processors.adoc)
- [../../docs/paths/configuration.adoc](../../docs/paths/configuration.adoc)
- [../../docs/paths/dlq.adoc](../../docs/paths/dlq.adoc)

## Goal

Replace AF4 root configuration lookups with AF5 event-processing APIs while
preserving named component behavior.

## Procedure

1. Find reads in the target class:

   | AF4 read | AF5 direction |
   |---|---|
   | `configuration.eventProcessingConfiguration().eventProcessor(name, ...)` | resolve named AF5 event processor/module |
   | `configuration.eventStore()` / `eventBus()` used for processing | route through AF5 event-processing module or storage-engine recipe |
   | `tokenStore(...)` | use AF5 token-store component only when supported; Mongo token store is blocked |
   | DLQ / dead-letter processor lookup | preserve named component and flag schema/support limits |

2. Replace injected/root type only as far as the caller needs. Do not migrate an
   entire configuration class from this addendum; route generic writes to
   `event-storage-engine/configuration.md`.
3. Keep processor names identical to `@Namespace` / registration names.
4. Update imports.
5. Verify the caller in the same isolated scope as the event processor target.

## Verify

- No AF4 event-processing configuration root call remains in the target.
- Named processor/token/DLQ lookups still use the same component name.
- Unsupported token/DLQ cases are recorded instead of silently dropped.
