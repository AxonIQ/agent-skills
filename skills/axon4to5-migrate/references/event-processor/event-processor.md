# Recipe: event-processor

Migrate one AF4 event-handling component: projector, projection updater,
reactor, or event processor configuration tied to that component.

## Canonical reference

- [../../docs/paths/projectors-event-processors.adoc](../../docs/paths/projectors-event-processors.adoc)
- [../../docs/paths/sequencing-policies.adoc](../../docs/paths/sequencing-policies.adoc)
- [../../docs/paths/dlq.adoc](../../docs/paths/dlq.adoc)
- [configuration-reads.md](configuration-reads.md) for direct `Configuration`
  reads.
- [not-supported.md](not-supported.md) for Mongo token store, saga handlers,
  and Kafka gaps.

## Goal

The component compiles on AF5, keeps its processing namespace, keeps event
ordering semantics, and preserves command/query side effects.

## Inputs

- `target`: event-handler FQCN or file path.
- `wiring`: `spring-boot` or `framework-config`.
- `target_test`: optional.

## Preflight

1. Run blocker checks from `not-supported.md`.
2. If this is a saga handler, emit `rejected` with `route-to:saga`.
3. If the class has no `@EventHandler`, emit `rejected`.
4. If the class already uses AF5 handler imports and verification is green,
   emit `skipped`.

## Procedure

1. **Identify the processing name.**
   - Prefer existing `@ProcessingGroup`.
   - Otherwise derive a stable namespace from registration/configuration.
   - If no name exists, use the class/simple component name and record it.

2. **Rewrite handler annotations.**
   - `@ProcessingGroup("<name>")` -> `@Namespace("<name>")`.
   - Move `@EventHandler` and sibling imports to AF5 packages.
   - Keep handler method signatures unless a removed AF4 parameter forces a
     targeted rewrite.

3. **Move gateway side effects to AF5 dispatchers.**

   | AF4 pattern inside handler | AF5 rewrite |
   |---|---|
   | field-injected `CommandGateway` used only in handlers | add `CommandDispatcher` method parameter and remove the field |
   | `sendAndWait` | `send(...).asCompletableFuture()` or chain async result |
   | gateway also used outside handlers | keep note for `command-gateway` follow-up |

4. **Preserve event ordering.**
   - Translate AF4 sequencing config to `@SequencingPolicy` when present.
   - Keep the same key expression/policy class.
   - If ordering was implicit and tests rely on it, record the assumption.

5. **Migrate processor configuration for this component.**

   | `wiring` | Action |
   |---|---|
   | `spring-boot` | Replace `EventProcessingConfigurer` registration for this processing group with an `EventProcessorDefinition` bean. Move relevant YAML/properties keys to AF5 equivalents. |
   | `framework-config` | Move registration into `MessagingConfigurer#eventProcessing(...)` / `EventProcessorModule` shape. |

   Keep DLQ decisions flag-only unless a supported AF5 target exists. Do not
   invent schema or token-store migration.

6. **Sweep direct configuration reads.**
   - If the class reads `eventProcessor`, `tokenStore`, or DLQ components from
     Axon `Configuration`, apply `configuration-reads.md`.

7. **Verify with `axon4to5-isolatedtest`.**
   - Include the handler class, event types, config class/YAML touched, and
     primary tests.

## End condition

- No AF4 event-handler imports remain in the target.
- Namespace and sequencing semantics are explicit.
- Touched processor configuration compiles.
- Scoped compile/tests pass, or the result is classified.

## Output

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQCN>
reason: <required except straightforward success>
decisions:
  namespace: <name>
  wiring: spring-boot | framework-config
  sequencing: preserved | none | deferred
  command-dispatch: none | rewritten | follow-up-command-gateway
  blockers: []
caller-expects:
  commit: true | false
  next: proceed | ask-user | record-and-skip | halt | route-to:<recipe>
notes: []
```

## Anti-patterns

- Do not silently drop DLQ, token store, error handler, or sequencing config.
- Do not leave a migrated handler with an AF4 `CommandGateway` field when that
  field is only used by handler methods.
- Do not route saga handlers through this recipe.
