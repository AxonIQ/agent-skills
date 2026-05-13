# Recipe: command-gateway

Migrate one top-of-chain caller that injects AF4 `CommandGateway`.

## Canonical reference

- [../../docs/paths/messages.adoc](../../docs/paths/messages.adoc)
- [../../docs/paths/index.adoc](../../docs/paths/index.adoc)
- [configuration-reads.md](configuration-reads.md) for direct command-bus reads.

## Goal

The caller dispatches commands through AF5 APIs while preserving blocking,
async, reactive, and callback behavior.

## Inputs

- `target`: caller FQCN or file path.
- `wiring`: `spring-boot` or `framework-config`.
- `target_test`: optional.

## Preflight

1. Reject classes that also declare handler/interceptor annotations; route them
   to the matching handler recipe first.
2. If no AF4 `CommandGateway` import/use remains, emit `skipped`.

## Procedure

1. Replace the injected `CommandGateway` type with the AF5 command dispatch API
   used by the project.
2. Rewrite each send call by return shape:

   | AF4 call shape | AF5 direction |
   |---|---|
   | fire-and-forget `send(...)` | dispatch async and keep existing future/void semantics |
   | blocking `sendAndWait(...)` | use async dispatch plus explicit blocking only where the old public method was blocking |
   | callbacks | translate callback success/failure handling to completion-stage style |
   | reactive wrapper | wrap the AF5 completion stage in the existing reactive type |

3. Preserve method signatures unless the old signature exposed AF4 types.
4. Update command message annotations per the canonical message doc.
5. If the class reads `commandBus()` from Axon `Configuration`, apply
   `configuration-reads.md`.
6. Verify with `axon4to5-isolatedtest`.

## End condition

- No AF4 `CommandGateway` import/use remains in the target.
- Public return behavior is preserved.
- Scoped compile/tests pass or the result is classified.

## Output

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQCN>
reason: <required except straightforward success>
decisions:
  dispatch-shapes: []
  blocking-preserved: true | false | n/a
caller-expects:
  commit: true | false
  next: proceed | ask-user | record-and-skip | halt | route-to:<recipe>
notes: []
```
